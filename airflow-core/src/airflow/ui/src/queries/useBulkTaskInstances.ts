/*!
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { useRef } from "react";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  useDagRunServiceGetDagRunKey,
  useDagRunServiceGetDagRunsKey,
  useDagRunServiceGetExecutionKey,
  useGanttServiceGetGanttDataKey,
  useTaskInstanceServiceBulkTaskInstances,
  useTaskInstanceServiceGetMappedTaskInstanceKey,
  useTaskInstanceServiceGetTaskInstanceKey,
  useTaskInstanceServiceGetTaskInstancesKey,
} from "openapi/queries";
import type { BulkBody_BulkTaskInstanceBody_, BulkResponse } from "openapi/requests/types.gen";

import { toaster } from "src/system-components";

import { gridQueryKeys, tiPerAttemptQueryKeys } from "./gridViewQueryKeys";
import { useClearTaskInstancesDryRunKey } from "./useClearTaskInstancesDryRun";
import { usePatchTaskInstanceDryRunKey } from "./usePatchTaskInstanceDryRun";

type Props = {
  readonly deselectKeys: (keys: Array<string>) => void;
  readonly onSuccessConfirm: VoidFunction;
};

export const useBulkTaskInstances = ({ deselectKeys, onSuccessConfirm }: Props) => {
  const queryClient = useQueryClient();
  const affectedDagIds = useRef<Set<string>>(new Set());
  const { t: translate } = useTranslation(["common", "dags"]);

  const onSuccess = async (responseData: BulkResponse) => {
    // Invalidate what usePatchTaskInstance does: lists, run and TI details, gantt, grid, and dry-run previews.
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: [useTaskInstanceServiceGetTaskInstancesKey] }),
      queryClient.invalidateQueries({ queryKey: [useDagRunServiceGetDagRunsKey] }),
      queryClient.invalidateQueries({ queryKey: [useDagRunServiceGetDagRunKey] }),
      queryClient.invalidateQueries({ queryKey: [useDagRunServiceGetExecutionKey] }),
      queryClient.invalidateQueries({ queryKey: [useTaskInstanceServiceGetTaskInstanceKey] }),
      queryClient.invalidateQueries({ queryKey: [useTaskInstanceServiceGetMappedTaskInstanceKey] }),
      queryClient.invalidateQueries({ queryKey: [useGanttServiceGetGanttDataKey] }),
      ...tiPerAttemptQueryKeys.map((key) => queryClient.invalidateQueries({ queryKey: key })),
      ...[...affectedDagIds.current].flatMap((dagId) => [
        ...gridQueryKeys(dagId).map((key) => queryClient.invalidateQueries({ queryKey: key })),
        queryClient.invalidateQueries({ queryKey: [useClearTaskInstancesDryRunKey, dagId] }),
        queryClient.invalidateQueries({ queryKey: [usePatchTaskInstanceDryRunKey, dagId] }),
      ]),
    ]);

    const isDelete = Boolean(responseData.delete);
    const actionResult = responseData.delete ?? responseData.update;
    const toasterKey = isDelete ? "toaster.bulkDelete" : "toaster.bulkUpdate";

    if (!actionResult) {
      return;
    }

    const successKeys = actionResult.success ?? [];
    const actionErrors = actionResult.errors ?? [];

    if (successKeys.length > 0) {
      toaster.create({
        description: translate(`${toasterKey}.success.description`, {
          count: successKeys.length,
          keys: successKeys.join(", "),
          resourceName: translate("taskInstance_other"),
        }),
        title: translate(`${toasterKey}.success.title`, {
          resourceName: translate("taskInstance_other"),
        }),
        type: "success",
      });
      deselectKeys(successKeys);
    }

    // Per-entity failures (status 200 with items in ``errors``) keep the dialog open
    // so the user can see what failed; the consumer renders ``data.<action>.errors``.
    if (actionErrors.length === 0) {
      onSuccessConfirm();
    }
  };

  const { data, error, isPending, mutate, reset } = useTaskInstanceServiceBulkTaskInstances({ onSuccess });

  const bulkAction = (requestBody: BulkBody_BulkTaskInstanceBody_) => {
    reset();
    const dagIds = new Set<string>();

    for (const action of requestBody.actions) {
      for (const entity of action.entities) {
        if (typeof entity !== "string" && entity.dag_id !== null && entity.dag_id !== undefined) {
          dagIds.add(entity.dag_id);
        }
      }
    }
    affectedDagIds.current = dagIds;
    mutate({ dagId: "~", dagRunId: "~", requestBody });
  };

  return { bulkAction, data, error, isPending, reset };
};
