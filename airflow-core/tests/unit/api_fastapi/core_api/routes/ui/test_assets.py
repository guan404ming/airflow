# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from unittest import mock

import pendulum
import pytest
from sqlalchemy import delete, select

from airflow.models.asset import (
    AssetDagRunQueue,
    AssetEvent,
    AssetModel,
    AssetPartitionDagRun,
    PartitionedAssetKeyLog,
)
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk.definitions.asset import Asset

from tests_common.test_utils.asserts import assert_queries_count
from tests_common.test_utils.db import clear_db_assets, clear_db_dags, clear_db_serialized_dags

pytestmark = pytest.mark.db_test


@pytest.fixture(autouse=True)
def cleanup():
    clear_db_dags()
    clear_db_serialized_dags()


class TestNextRunAssets:
    def test_should_response_200(self, test_client, dag_maker):
        with dag_maker(
            dag_id="upstream",
            schedule=[Asset(uri="s3://bucket/next-run-asset/1", name="asset1")],
            serialized=True,
        ):
            EmptyOperator(task_id="task1")

        dag_maker.create_dagrun()
        dag_maker.sync_dagbag_to_db()

        with assert_queries_count(4):
            response = test_client.get("/next_run_assets/upstream")

        assert response.status_code == 200
        assert response.json() == {
            "asset_expression": {
                "all": [
                    {
                        "asset": {
                            "uri": "s3://bucket/next-run-asset/1",
                            "name": "asset1",
                            "group": "asset",
                            "id": mock.ANY,
                        }
                    }
                ]
            },
            "events": [
                {"id": mock.ANY, "uri": "s3://bucket/next-run-asset/1", "name": "asset1", "lastUpdate": None}
            ],
        }

    def test_should_respond_401(self, unauthenticated_test_client):
        response = unauthenticated_test_client.get("/next_run_assets/upstream")
        assert response.status_code == 401

    def test_should_respond_403(self, unauthorized_test_client):
        response = unauthorized_test_client.get("/next_run_assets/upstream")
        assert response.status_code == 403

    def test_should_set_last_update_only_for_queued_and_hide_flag(self, test_client, dag_maker, session):
        with dag_maker(
            dag_id="two_assets_equal",
            schedule=[
                Asset(uri="s3://bucket/A", name="A"),
                Asset(uri="s3://bucket/B", name="B"),
            ],
            serialized=True,
        ):
            EmptyOperator(task_id="t")

        dr = dag_maker.create_dagrun()
        dag_maker.sync_dagbag_to_db()

        assets = {
            a.uri: a
            for a in session.scalars(
                select(AssetModel).where(AssetModel.uri.in_(["s3://bucket/A", "s3://bucket/B"]))
            )
        }
        # Queue and add an event only for A
        session.add(AssetDagRunQueue(asset_id=assets["s3://bucket/A"].id, target_dag_id="two_assets_equal"))
        session.add(
            AssetEvent(asset_id=assets["s3://bucket/A"].id, timestamp=dr.logical_date or pendulum.now())
        )
        session.commit()

        response = test_client.get("/next_run_assets/two_assets_equal")
        assert response.status_code == 200
        assert response.json() == {
            "asset_expression": {
                "all": [
                    {
                        "asset": {
                            "uri": "s3://bucket/A",
                            "name": "A",
                            "group": "asset",
                            "id": mock.ANY,
                        }
                    },
                    {
                        "asset": {
                            "uri": "s3://bucket/B",
                            "name": "B",
                            "group": "asset",
                            "id": mock.ANY,
                        }
                    },
                ]
            },
            # events are ordered by uri
            "events": [
                {"id": mock.ANY, "uri": "s3://bucket/A", "name": "A", "lastUpdate": mock.ANY},
                {"id": mock.ANY, "uri": "s3://bucket/B", "name": "B", "lastUpdate": None},
            ],
        }

    def test_last_update_respects_latest_run_filter(self, test_client, dag_maker, session):
        with dag_maker(
            dag_id="filter_run",
            schedule=[Asset(uri="s3://bucket/F", name="F")],
            serialized=True,
        ):
            EmptyOperator(task_id="t")

        dr = dag_maker.create_dagrun()
        dag_maker.sync_dagbag_to_db()

        asset = session.scalars(select(AssetModel).where(AssetModel.uri == "s3://bucket/F")).one()
        session.add(AssetDagRunQueue(asset_id=asset.id, target_dag_id="filter_run"))
        # event before latest_run should be ignored
        ts_base = dr.logical_date or pendulum.now()
        session.add(AssetEvent(asset_id=asset.id, timestamp=ts_base.subtract(minutes=10)))
        # event after latest_run counts
        session.add(AssetEvent(asset_id=asset.id, timestamp=ts_base.add(minutes=10)))
        session.commit()

        resp = test_client.get("/next_run_assets/filter_run")
        assert resp.status_code == 200
        ev = resp.json()["events"][0]
        assert ev["lastUpdate"] is not None
        assert "queued" not in ev


class TestGetPendingAssetPartitions:
    @pytest.fixture(autouse=True)
    def setup(self, session):
        session.execute(delete(PartitionedAssetKeyLog))
        session.execute(delete(AssetPartitionDagRun))
        session.commit()
        clear_db_assets()
        clear_db_dags()
        clear_db_serialized_dags()
        yield
        session.execute(delete(PartitionedAssetKeyLog))
        session.execute(delete(AssetPartitionDagRun))
        session.commit()
        clear_db_assets()
        clear_db_dags()
        clear_db_serialized_dags()

    def _create_dag_and_assets(self, dag_maker, session):
        """Create a DAG scheduled on 3 assets and return the asset models."""
        with dag_maker(
            dag_id="partitioned_consumer",
            schedule=[
                Asset(uri="s3://bucket/sales", name="sales"),
                Asset(uri="s3://bucket/inventory", name="inventory"),
                Asset(uri="s3://bucket/pricing", name="pricing"),
            ],
            serialized=True,
        ):
            EmptyOperator(task_id="consume")

        dag_maker.create_dagrun()
        dag_maker.sync_dagbag_to_db()

        assets = {
            a.name: a
            for a in session.scalars(
                select(AssetModel).where(
                    AssetModel.uri.in_(["s3://bucket/sales", "s3://bucket/inventory", "s3://bucket/pricing"])
                )
            )
        }
        return assets

    def _create_pending_partition(self, session, partition_key, assets_received, all_assets):
        """Create an AssetPartitionDagRun and PartitionedAssetKeyLog entries."""
        apdr = AssetPartitionDagRun(
            target_dag_id="partitioned_consumer",
            partition_key=partition_key,
        )
        session.add(apdr)
        session.flush()

        for asset_name in assets_received:
            asset = all_assets[asset_name]
            event = AssetEvent(asset_id=asset.id, partition_key=partition_key)
            session.add(event)
            session.flush()
            session.add(
                PartitionedAssetKeyLog(
                    asset_id=asset.id,
                    asset_event_id=event.id,
                    asset_partition_dag_run_id=apdr.id,
                    source_partition_key=partition_key,
                    target_dag_id="partitioned_consumer",
                    target_partition_key=partition_key,
                )
            )
        session.commit()
        return apdr

    def test_should_respond_200_empty(self, test_client, dag_maker, session):
        self._create_dag_and_assets(dag_maker, session)

        response = test_client.get("/dags/partitioned_consumer/asset_partitions/pending")
        assert response.status_code == 200
        assert response.json() == {"pending_partitions": [], "total_entries": 0}

    def test_should_respond_200_with_partitions(self, test_client, dag_maker, session):
        assets = self._create_dag_and_assets(dag_maker, session)

        # Partition with 2/3 assets received
        self._create_pending_partition(session, "2024-01-15", ["sales", "inventory"], assets)
        # Partition with 1/3 assets received
        self._create_pending_partition(session, "2024-01-16", ["sales"], assets)

        response = test_client.get("/dags/partitioned_consumer/asset_partitions/pending")
        assert response.status_code == 200
        body = response.json()
        assert body["total_entries"] == 2
        assert len(body["pending_partitions"]) == 2

        # Ordered by created_at desc, so 2024-01-16 first
        p1 = body["pending_partitions"][0]
        assert p1["partition_key"] == "2024-01-16"
        assert p1["received_count"] == 1
        assert p1["total_required"] == 3
        assert len(p1["received_assets"]) == 1
        assert p1["received_assets"][0]["name"] == "sales"

        p2 = body["pending_partitions"][1]
        assert p2["partition_key"] == "2024-01-15"
        assert p2["received_count"] == 2
        assert p2["total_required"] == 3
        assert len(p2["received_assets"]) == 2

    def test_should_respond_200_pagination(self, test_client, dag_maker, session):
        assets = self._create_dag_and_assets(dag_maker, session)

        for i in range(5):
            self._create_pending_partition(session, f"2024-01-{10 + i:02d}", ["sales"], assets)

        response = test_client.get("/dags/partitioned_consumer/asset_partitions/pending?limit=2&offset=0")
        assert response.status_code == 200
        body = response.json()
        assert body["total_entries"] == 5
        assert len(body["pending_partitions"]) == 2

        response2 = test_client.get("/dags/partitioned_consumer/asset_partitions/pending?limit=2&offset=2")
        assert response2.status_code == 200
        body2 = response2.json()
        assert body2["total_entries"] == 5
        assert len(body2["pending_partitions"]) == 2

    def test_should_not_include_completed_partitions(self, test_client, dag_maker, session):
        assets = self._create_dag_and_assets(dag_maker, session)

        # Pending partition
        self._create_pending_partition(session, "2024-01-15", ["sales"], assets)

        # Completed partition (created_dag_run_id is set)
        completed = AssetPartitionDagRun(
            target_dag_id="partitioned_consumer",
            partition_key="2024-01-14",
            created_dag_run_id=1,
        )
        session.add(completed)
        session.commit()

        response = test_client.get("/dags/partitioned_consumer/asset_partitions/pending")
        assert response.status_code == 200
        body = response.json()
        assert body["total_entries"] == 1
        assert body["pending_partitions"][0]["partition_key"] == "2024-01-15"

    def test_should_respond_404_for_unknown_dag(self, test_client):
        response = test_client.get("/dags/nonexistent_dag/asset_partitions/pending")
        assert response.status_code == 404

    def test_should_respond_401(self, unauthenticated_test_client):
        response = unauthenticated_test_client.get("/dags/any_dag/asset_partitions/pending")
        assert response.status_code == 401

    def test_should_respond_403(self, unauthorized_test_client):
        response = unauthorized_test_client.get("/dags/any_dag/asset_partitions/pending")
        assert response.status_code == 403
