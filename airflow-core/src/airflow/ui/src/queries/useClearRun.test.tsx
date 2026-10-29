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
  UseDagServiceGetDagRunStateCountsUiKeyFn,
  UseDagServiceGetDagsUiKeyFn,
  UseDagServiceGetRecentTaskInstanceStateCountsUiKeyFn,
} from "openapi/queries";
import { DagRunService } from "openapi/requests";
import type { DAGRunResponse } from "openapi/requests/types.gen";

import { useBulkClearDagRuns } from "./useBulkClearDagRuns";
import { useClearDagRun } from "./useClearRun";

const dagRun = { dag_id: "dag", dag_run_id: "run" } as DAGRunResponse;

const useClearSingleRun = (onSuccessConfirm: VoidFunction) => {
  const { mutate } = useClearDagRun({ dagId: "dag", dagRunId: "run", onSuccessConfirm });

  return () => mutate({ dagId: "dag", dagRunId: "run", requestBody: { dry_run: false } });
};

const useClearMultipleRuns = (onSuccessConfirm: VoidFunction) => {
  const { bulkClear } = useBulkClearDagRuns({ deselectKeys: vi.fn(), onSuccessConfirm });

  return () => bulkClear([dagRun], { note: null, onlyFailed: false, onlyNew: false });
};

describe.each([
  { operation: "single-run clear", useClear: useClearSingleRun },
  { operation: "bulk-run clear", useClear: useClearMultipleRuns },
])("Dag card cache after $operation", ({ useClear }) => {
  beforeEach(() => {
    vi.spyOn(DagRunService, "clearDagRun").mockResolvedValue({ task_instances: [], total_entries: 0 });
    vi.spyOn(DagRunService, "clearDagRuns").mockResolvedValue({ dag_runs: [dagRun], total_entries: 1 });
  });
  afterEach(() => vi.restoreAllMocks());

  it.each([
    { name: "Dag list", queryKey: UseDagServiceGetDagsUiKeyFn({ limit: 50 }) },
    { name: "run-state counts", queryKey: UseDagServiceGetDagRunStateCountsUiKeyFn({ dagIds: ["dag"] }) },
    {
      name: "recent task-state counts",
      queryKey: UseDagServiceGetRecentTaskInstanceStateCountsUiKeyFn({ dagRunIds: [1] }),
    },
  ])("invalidates the cached $name before navigating back", async ({ queryKey }) => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: Infinity } } });

    queryClient.setQueryData(queryKey, { cached: true });
    const wrapper = ({ children }: PropsWithChildren) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const onSuccessConfirm = vi.fn();
    const { result } = renderHook(() => useClear(onSuccessConfirm), { wrapper });

    act(() => result.current());
    await waitFor(() => expect(onSuccessConfirm).toHaveBeenCalled());
    expect(queryClient.getQueryState(queryKey)?.isInvalidated).toBe(true);
    queryClient.clear();
  });
});
