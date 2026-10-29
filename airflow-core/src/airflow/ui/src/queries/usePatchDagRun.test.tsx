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

import { useBulkPatchDagRun } from "./useBulkPatchDagRun";
import { usePatchDagRun } from "./usePatchDagRun";

const useMarkSingleRun = (onSuccess: VoidFunction) => {
  const { mutate } = usePatchDagRun({ dagId: "dag", dagRunId: "run", onSuccess });

  return () => mutate({ dagId: "dag", dagRunId: "run", requestBody: { state: "success" } });
};

const useMarkMultipleRuns = (onSuccessConfirm: VoidFunction) => {
  const { bulkAction } = useBulkPatchDagRun({ deselectKeys: vi.fn(), onSuccessConfirm });

  return () =>
    bulkAction({
      actions: [{ action: "update", entities: [{ dag_id: "dag", dag_run_id: "run", state: "success" }] }],
    });
};

describe.each([
  { operation: "single-run mark", useMark: useMarkSingleRun },
  { operation: "bulk-run mark", useMark: useMarkMultipleRuns },
])("Dag card cache after $operation", ({ useMark }) => {
  beforeEach(() => {
    vi.spyOn(DagRunService, "patchDagRun").mockResolvedValue({
      dag_id: "dag",
      dag_run_id: "run",
    } as DAGRunResponse);
    vi.spyOn(DagRunService, "bulkDagRuns").mockResolvedValue({
      update: { errors: [], success: ["dag.run"] },
    });
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
    const { result } = renderHook(() => useMark(onSuccessConfirm), { wrapper });

    act(() => result.current());
    await waitFor(() => expect(onSuccessConfirm).toHaveBeenCalled());
    expect(queryClient.getQueryState(queryKey)?.isInvalidated).toBe(true);
    queryClient.clear();
  });
});
