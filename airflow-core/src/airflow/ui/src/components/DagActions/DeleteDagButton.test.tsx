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

import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DagsListSearchContext } from "src/context/dagsListSearch";
import { server } from "src/mocks/server";
import { BaseWrapper } from "src/utils/Wrapper";

import { DeleteDagButton } from "./DeleteDagButton";

const CurrentLocation = () => {
  const { pathname, search } = useLocation();

  return <output>{`${pathname}${search}`}</output>;
};

const wrapper = ({ children }: PropsWithChildren) => (
  <BaseWrapper>
    <MemoryRouter initialEntries={["/dags/example_dag"]}>
      <DagsListSearchContext.Provider value="tags=example">
        {children}
        <CurrentLocation />
      </DagsListSearchContext.Provider>
    </MemoryRouter>
  </BaseWrapper>
);

describe("DeleteDagButton", () => {
  it("returns to the Dags page with the remembered list query after a delete on the Dag page", async () => {
    server.use(http.delete("*/api/v2/dags/:dagId", () => new HttpResponse(null, { status: 204 })));
    render(<DeleteDagButton dagDisplayName="example_dag" dagId="example_dag" />, { wrapper });

    fireEvent.click(screen.getByRole("button", { name: "dagActions.delete.button" }));
    fireEvent.click(await screen.findByTestId("delete-confirm-button"));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("/dags?tags=example"));
  });
});
