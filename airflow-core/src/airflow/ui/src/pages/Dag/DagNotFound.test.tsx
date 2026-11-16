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
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DagsListSearchContext } from "src/context/dagsListSearch";
import { BaseWrapper } from "src/utils/Wrapper";

import { DagNotFound } from "./DagNotFound";

const CurrentLocation = () => {
  const { pathname, search } = useLocation();

  return <output>{`${pathname}${search}`}</output>;
};

const wrapper = ({ children }: PropsWithChildren) => (
  <BaseWrapper>
    <MemoryRouter initialEntries={["/dags/missing_dag"]}>
      <DagsListSearchContext.Provider value="tags=example">
        {children}
        <CurrentLocation />
      </DagsListSearchContext.Provider>
    </MemoryRouter>
  </BaseWrapper>
);

describe("DagNotFound", () => {
  it("goes back to the Dags page with the remembered list query", () => {
    render(<DagNotFound dagId="missing_dag" />, { wrapper });

    fireEvent.click(screen.getByRole("button", { name: "notFound.backToDags" }));

    expect(screen.getByRole("status")).toHaveTextContent("/dags?tags=example");
  });
});
