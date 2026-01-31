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
import { Badge, Box, Heading, HStack, List, Text } from "@chakra-ui/react";
import type { ColumnDef } from "@tanstack/react-table";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

import { useAssetServiceGetPendingAssetPartitions } from "openapi/queries";
import type { PendingPartitionResponse } from "openapi/requests/types.gen";
import { DataTable } from "src/components/DataTable";
import { useTableURLState } from "src/components/DataTable/useTableUrlState";
import { ErrorAlert } from "src/components/ErrorAlert";
import Time from "src/components/Time";
import { Popover } from "src/components/ui";

const StatusBadge = ({
  label,
  received,
  total,
}: {
  readonly label: string;
  readonly received: number;
  readonly total: number;
}) => {
  const colorPalette = received >= total ? "green" : received > 0 ? "yellow" : "red";

  return (
    <Badge colorPalette={colorPalette} variant="subtle">
      {received}/{total} {label}
    </Badge>
  );
};

const getColumns = (translate: (key: string) => string): Array<ColumnDef<PendingPartitionResponse>> => [
  {
    accessorKey: "partition_key",
    enableSorting: false,
    header: translate("dag:partitions.partitionKey"),
  },
  {
    accessorKey: "status",
    cell: ({ row }) => (
      <StatusBadge
        label={translate("dag:partitions.assets")}
        received={row.original.received_count}
        total={row.original.total_required}
      />
    ),
    enableSorting: false,
    header: translate("dag:partitions.status"),
  },
  {
    accessorKey: "received_assets",
    cell: ({ row }) => {
      const receivedAssets = row.original.received_assets;

      if (receivedAssets.length === 0) {
        return <Text color="fg.muted">--</Text>;
      }

      return (
        <Popover.Root lazyMount positioning={{ placement: "bottom-start" }} unmountOnExit>
          <Popover.Trigger asChild>
            <Badge cursor="pointer" variant="outline">
              {receivedAssets.length} {translate("dag:partitions.assetsReceived")}
            </Badge>
          </Popover.Trigger>
          <Popover.Content css={{ "--popover-bg": "colors.bg.emphasized" }} width="fit-content">
            <Popover.Arrow />
            <Popover.Body>
              <List.Root gap={1}>
                {receivedAssets.map((asset) => (
                  <List.Item key={asset.asset_id}>
                    <HStack>
                      <Text fontWeight="medium">{asset.name}</Text>
                      {asset.source_partition_key !== null && asset.source_partition_key !== undefined ? (
                        <Text color="fg.muted" fontSize="sm">
                          ({asset.source_partition_key})
                        </Text>
                      ) : undefined}
                    </HStack>
                  </List.Item>
                ))}
              </List.Root>
            </Popover.Body>
          </Popover.Content>
        </Popover.Root>
      );
    },
    enableSorting: false,
    header: translate("dag:partitions.receivedAssets"),
  },
  {
    accessorKey: "created_at",
    cell: ({ row }) => (
      <Text>
        <Time datetime={row.original.created_at} />
      </Text>
    ),
    enableSorting: false,
    header: translate("dag:partitions.createdAt"),
  },
];

export const Partitions = () => {
  const { t: translate } = useTranslation();
  const { setTableURLState, tableURLState } = useTableURLState();
  const { pagination } = tableURLState;
  const { dagId = "" } = useParams();

  const { data, error, isFetching, isLoading } = useAssetServiceGetPendingAssetPartitions({
    dagId,
    limit: pagination.pageSize,
    offset: pagination.pageIndex * pagination.pageSize,
  });

  const columns = getColumns(translate);

  return (
    <Box>
      <ErrorAlert error={error} />
      <Heading my={1} size="md">
        {translate("dag:partitions.title", { count: data ? data.total_entries : 0 })}
      </Heading>
      <DataTable
        columns={columns}
        data={data ? data.pending_partitions : []}
        isFetching={isFetching}
        isLoading={isLoading}
        modelName="dag:partitions.partition"
        onStateChange={setTableURLState}
        total={data ? data.total_entries : 0}
      />
    </Box>
  );
};
