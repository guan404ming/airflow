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
import { afterEach, expect, it, vi } from "vitest";

import {
  UseDagRunServiceGetDagRunKeyFn,
  UseDagRunServiceGetDagRunsKeyFn,
  UseDagRunServiceGetExecutionKeyFn,
  UseGanttServiceGetGanttDataKeyFn,
  UseTaskInstanceServiceGetMappedTaskInstanceKeyFn,
  UseTaskInstanceServiceGetTaskInstanceKeyFn,
} from "openapi/queries";
import { TaskInstanceService } from "openapi/requests";

import { usePatchTaskGroup } from "./usePatchTaskGroup";
import { usePatchTaskInstanceDryRunKey } from "./usePatchTaskInstanceDryRun";

afterEach(() => vi.restoreAllMocks());

it.each([
  { name: "run", queryKey: UseDagRunServiceGetDagRunKeyFn({ dagId: "dag", dagRunId: "run" }) },
  { name: "run list", queryKey: UseDagRunServiceGetDagRunsKeyFn({ dagId: "dag" }) },
  { name: "run execution", queryKey: UseDagRunServiceGetExecutionKeyFn({ dagId: "dag", dagRunId: "run" }) },
  { name: "Gantt", queryKey: UseGanttServiceGetGanttDataKeyFn({ dagId: "dag", runId: "run" }) },
  {
    name: "task instance",
    queryKey: UseTaskInstanceServiceGetTaskInstanceKeyFn({
      dagId: "dag",
      dagRunId: "run",
      taskId: "group.work",
    }),
  },
  {
    name: "mapped task instance",
    queryKey: UseTaskInstanceServiceGetMappedTaskInstanceKeyFn({
      dagId: "dag",
      dagRunId: "run",
      mapIndex: 0,
      taskId: "group.work",
    }),
  },
  {
    name: "mark dry run",
    queryKey: [usePatchTaskInstanceDryRunKey, "dag", "run", { mapIndex: 0, taskId: "group.work" }],
  },
])("invalidates the cached $name after marking a task group", async ({ queryKey }) => {
  vi.spyOn(TaskInstanceService, "patchTaskGroupInstances").mockResolvedValue({
    task_instances: [],
    total_entries: 0,
  });
  const queryClient = new QueryClient();

  queryClient.setQueryData(queryKey, {});

  const wrapper = ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const onSuccess = vi.fn();
  const { result } = renderHook(
    () => usePatchTaskGroup({ dagId: "dag", dagRunId: "run", groupId: "group", onSuccess }),
    { wrapper },
  );

  act(() =>
    result.current.mutate({
      dagId: "dag",
      dagRunId: "run",
      groupId: "group",
      requestBody: { new_state: "success" },
    }),
  );

  await waitFor(() => expect(onSuccess).toHaveBeenCalled());
  expect(queryClient.getQueryState(queryKey)?.isInvalidated).toBe(true);
});
