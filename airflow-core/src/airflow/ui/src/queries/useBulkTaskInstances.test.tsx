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
import type { PropsWithChildren } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  UseDagRunServiceGetDagRunKeyFn,
  UseGanttServiceGetGanttDataKeyFn,
  UseGridServiceGetGridRunsKeyFn,
  UseTaskInstanceServiceGetTaskInstanceKeyFn,
} from "openapi/queries";
import { TaskInstanceService } from "openapi/requests";
import type { BulkBody_BulkTaskInstanceBody_, BulkResponse } from "openapi/requests/types.gen";

import { useBulkTaskInstances } from "./useBulkTaskInstances";
import { useClearTaskInstancesDryRunKey } from "./useClearTaskInstancesDryRun";
import { usePatchTaskInstanceDryRunKey } from "./usePatchTaskInstanceDryRun";

const entity = { dag_id: "dag", dag_run_id: "run", map_index: -1, task_id: "task" };

const operations: Array<{
  operation: string;
  requestBody: BulkBody_BulkTaskInstanceBody_;
  response: BulkResponse;
}> = [
  {
    operation: "bulk mark",
    requestBody: { actions: [{ action: "update", entities: [{ ...entity, new_state: "success" }] }] },
    response: { update: { errors: [], success: ["dag.run.task[-1]"] } },
  },
  {
    operation: "bulk delete",
    requestBody: { actions: [{ action: "delete", entities: [entity] }] },
    response: { delete: { errors: [], success: ["dag.run.task[-1]"] } },
  },
];

describe.each(operations)("Grid and run caches after $operation", ({ requestBody, response }) => {
  beforeEach(() => {
    vi.spyOn(TaskInstanceService, "bulkTaskInstances").mockResolvedValue(response);
  });
  afterEach(() => vi.restoreAllMocks());

  it.each([
    {
      name: "grid runs",
      queryKey: UseGridServiceGetGridRunsKeyFn({ dagId: "dag", limit: 10, orderBy: ["-run_after"] }),
    },
    { name: "run details", queryKey: UseDagRunServiceGetDagRunKeyFn({ dagId: "dag", dagRunId: "run" }) },
    {
      name: "task instance details",
      queryKey: UseTaskInstanceServiceGetTaskInstanceKeyFn({ dagId: "dag", dagRunId: "run", taskId: "task" }),
    },
    { name: "gantt data", queryKey: UseGanttServiceGetGanttDataKeyFn({ dagId: "dag", runId: "run" }) },
    { name: "clear dry run", queryKey: [useClearTaskInstancesDryRunKey, "dag", { dag_run_id: "run" }] },
    {
      name: "mark dry run",
      queryKey: [usePatchTaskInstanceDryRunKey, "dag", "run", { mapIndex: -1, taskId: "task" }],
    },
  ])("invalidates the cached $name", async ({ queryKey }) => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } });

    queryClient.setQueryData(queryKey, { cached: true });
    const wrapper = ({ children }: PropsWithChildren) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const onSuccessConfirm = vi.fn();
    const { result } = renderHook(() => useBulkTaskInstances({ deselectKeys: vi.fn(), onSuccessConfirm }), {
      wrapper,
    });

    act(() => result.current.bulkAction(requestBody));
    await waitFor(() => expect(onSuccessConfirm).toHaveBeenCalled());
    expect(queryClient.getQueryState(queryKey)?.isInvalidated).toBe(true);
    queryClient.clear();
  });
});
