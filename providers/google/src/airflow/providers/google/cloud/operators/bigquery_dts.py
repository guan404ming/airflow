#
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
"""This module contains Google BigQuery Data Transfer Service operators."""

from __future__ import annotations

import time
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING

from google.api_core.gapic_v1.method import DEFAULT, _MethodDefault
from google.cloud.bigquery_datatransfer_v1 import (
    StartManualTransferRunsResponse,
    TransferConfig,
    TransferRun,
    TransferState,
)

from airflow.configuration import conf
from airflow.exceptions import AirflowException
from airflow.providers.google.cloud.hooks.bigquery_dts import BiqQueryDataTransferServiceHook, get_object_id
from airflow.providers.google.cloud.links.bigquery_dts import BigQueryDataTransferConfigLink
from airflow.providers.google.cloud.operators.cloud_base import GoogleCloudBaseOperator
from airflow.providers.google.cloud.triggers.bigquery_dts import BigQueryDataTransferRunTrigger
from airflow.providers.google.common.hooks.base_google import PROVIDE_PROJECT_ID

if TYPE_CHECKING:
    from google.api_core.retry import Retry

    from airflow.utils.context import Context


def _get_transfer_config_details(config_transfer_name: str):
    config_details = config_transfer_name.split("/")
    return {"project_id": config_details[1], "region": config_details[3], "config_id": config_details[5]}


class BigQueryCreateDataTransferOperator(GoogleCloudBaseOperator):
    """
    Creates a new data transfer configuration.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:BigQueryCreateDataTransferOperator`

    :param transfer_config: Data transfer configuration to create.
    :param project_id: The BigQuery project id where the transfer configuration should be
            created. If set to None or missing, the default project_id from the Google Cloud connection
            is used.
    :param location: BigQuery Transfer Service location for regional transfers.
    :param authorization_code: authorization code to use with this transfer configuration.
        This is required if new credentials are needed.
    :param retry: A retry object used to retry requests. If `None` is
        specified, requests will not be retried.
    :param timeout: The amount of time, in seconds, to wait for the request to
        complete. Note that if retry is specified, the timeout applies to each individual
        attempt.
    :param metadata: Additional metadata that is provided to the method.
    :param gcp_conn_id: The connection ID used to connect to Google Cloud.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    """

    template_fields: Sequence[str] = (
        "transfer_config",
        "project_id",
        "authorization_code",
        "gcp_conn_id",
        "impersonation_chain",
    )
    operator_extra_links = (BigQueryDataTransferConfigLink(),)

    def __init__(
        self,
        *,
        transfer_config: dict,
        project_id: str = PROVIDE_PROJECT_ID,
        location: str | None = None,
        authorization_code: str | None = None,
        retry: Retry | _MethodDefault = DEFAULT,
        timeout: float | None = None,
        metadata: Sequence[tuple[str, str]] = (),
        gcp_conn_id="google_cloud_default",
        impersonation_chain: str | Sequence[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.transfer_config = transfer_config
        self.authorization_code = authorization_code
        self.project_id = project_id
        self.location = location
        self.retry = retry
        self.timeout = timeout
        self.metadata = metadata
        self.gcp_conn_id = gcp_conn_id
        self.impersonation_chain = impersonation_chain

    def execute(self, context: Context):
        hook = BiqQueryDataTransferServiceHook(
            gcp_conn_id=self.gcp_conn_id, impersonation_chain=self.impersonation_chain, location=self.location
        )
        self.log.info("Creating DTS transfer config")
        response = hook.create_transfer_config(
            project_id=self.project_id,
            transfer_config=self.transfer_config,
            authorization_code=self.authorization_code,
            retry=self.retry,
            timeout=self.timeout,
            metadata=self.metadata,
        )

        transfer_config = _get_transfer_config_details(response.name)
        BigQueryDataTransferConfigLink.persist(
            context=context,
            region=transfer_config["region"],
            config_id=transfer_config["config_id"],
            project_id=transfer_config["project_id"],
        )

        result = TransferConfig.to_dict(response)
        self.log.info("Created DTS transfer config %s", get_object_id(result))
        context["ti"].xcom_push(key="transfer_config_id", value=get_object_id(result))
        # don't push AWS secret in XCOM
        result.get("params", {}).pop("secret_access_key", None)
        result.get("params", {}).pop("access_key_id", None)
        return result


class BigQueryDeleteDataTransferConfigOperator(GoogleCloudBaseOperator):
    """
    Deletes transfer configuration.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:BigQueryDeleteDataTransferConfigOperator`

    :param transfer_config_id: Id of transfer config to be used.
    :param project_id: The BigQuery project id where the transfer configuration should be
        created. If set to None or missing, the default project_id from the Google Cloud connection is used.
    :param location: BigQuery Transfer Service location for regional transfers.
    :param retry: A retry object used to retry requests. If `None` is
        specified, requests will not be retried.
    :param timeout: The amount of time, in seconds, to wait for the request to
        complete. Note that if retry is specified, the timeout applies to each individual
        attempt.
    :param metadata: Additional metadata that is provided to the method.
    :param gcp_conn_id: The connection ID used to connect to Google Cloud.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    """

    template_fields: Sequence[str] = (
        "transfer_config_id",
        "project_id",
        "gcp_conn_id",
        "impersonation_chain",
    )

    def __init__(
        self,
        *,
        transfer_config_id: str,
        project_id: str = PROVIDE_PROJECT_ID,
        location: str | None = None,
        retry: Retry | _MethodDefault = DEFAULT,
        timeout: float | None = None,
        metadata: Sequence[tuple[str, str]] = (),
        gcp_conn_id="google_cloud_default",
        impersonation_chain: str | Sequence[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.project_id = project_id
        self.location = location
        self.transfer_config_id = transfer_config_id
        self.retry = retry
        self.timeout = timeout
        self.metadata = metadata
        self.gcp_conn_id = gcp_conn_id
        self.impersonation_chain = impersonation_chain

    def execute(self, context: Context) -> None:
        hook = BiqQueryDataTransferServiceHook(
            gcp_conn_id=self.gcp_conn_id, impersonation_chain=self.impersonation_chain, location=self.location
        )
        hook.delete_transfer_config(
            transfer_config_id=self.transfer_config_id,
            project_id=self.project_id,
            retry=self.retry,
            timeout=self.timeout,
            metadata=self.metadata,
        )


class BigQueryDataTransferServiceStartTransferRunsOperator(GoogleCloudBaseOperator):
    """
    Start manual transfer runs to be executed now with schedule_time equal to current time.

    The transfer runs can be created for a time range where the run_time is between
    start_time (inclusive) and end_time (exclusive), or for a specific run_time.

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:BigQueryDataTransferServiceStartTransferRunsOperator`

    :param transfer_config_id: Id of transfer config to be used.
    :param requested_time_range: Time range for the transfer runs that should be started.
        If a dict is provided, it must be of the same form as the protobuf
        message `~google.cloud.bigquery_datatransfer_v1.types.TimeRange`
    :param requested_run_time: Specific run_time for a transfer run to be started. The
        requested_run_time must not be in the future.  If a dict is provided, it
        must be of the same form as the protobuf message
        `~google.cloud.bigquery_datatransfer_v1.types.Timestamp`
    :param project_id: The BigQuery project id where the transfer configuration should be
        created.
    :param location: BigQuery Transfer Service location for regional transfers.
    :param retry: A retry object used to retry requests. If `None` is
        specified, requests will not be retried.
    :param timeout: The amount of time, in seconds, to wait for the request to
        complete. Note that if retry is specified, the timeout applies to each individual
        attempt.
    :param metadata: Additional metadata that is provided to the method.
    :param gcp_conn_id: The connection ID used to connect to Google Cloud.
    :param impersonation_chain: Optional service account to impersonate using short-term
        credentials, or chained list of accounts required to get the access_token
        of the last account in the list, which will be impersonated in the request.
        If set as a string, the account must grant the originating account
        the Service Account Token Creator IAM role.
        If set as a sequence, the identities from the list must grant
        Service Account Token Creator IAM role to the directly preceding identity, with first
        account from the list granting this role to the originating account (templated).
    :param deferrable: Run operator in the deferrable mode.
    """

    template_fields: Sequence[str] = (
        "transfer_config_id",
        "project_id",
        "requested_time_range",
        "requested_run_time",
        "gcp_conn_id",
        "impersonation_chain",
    )
    operator_extra_links = (BigQueryDataTransferConfigLink(),)

    def __init__(
        self,
        *,
        transfer_config_id: str,
        project_id: str = PROVIDE_PROJECT_ID,
        location: str | None = None,
        requested_time_range: dict | None = None,
        requested_run_time: dict | None = None,
        retry: Retry | _MethodDefault = DEFAULT,
        timeout: float | None = None,
        metadata: Sequence[tuple[str, str]] = (),
        gcp_conn_id="google_cloud_default",
        impersonation_chain: str | Sequence[str] | None = None,
        deferrable: bool = conf.getboolean("operators", "default_deferrable", fallback=False),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.project_id = project_id
        self.location = location
        self.transfer_config_id = transfer_config_id
        self.requested_time_range = requested_time_range
        self.requested_run_time = requested_run_time
        self.retry = retry
        self.timeout = timeout
        self.metadata = metadata
        self.gcp_conn_id = gcp_conn_id
        self.impersonation_chain = impersonation_chain
        self.deferrable = deferrable
        self._transfer_run: dict = {}

    @cached_property
    def hook(self) -> BiqQueryDataTransferServiceHook:
        hook = BiqQueryDataTransferServiceHook(
            gcp_conn_id=self.gcp_conn_id,
            impersonation_chain=self.impersonation_chain,
            location=self.location,
        )
        return hook

    def execute(self, context: Context):
        self.log.info("Submitting manual transfer for %s", self.transfer_config_id)

        if self.requested_run_time and isinstance(self.requested_run_time.get("seconds"), str):
            self.requested_run_time["seconds"] = int(self.requested_run_time["seconds"])

        response = self.hook.start_manual_transfer_runs(
            transfer_config_id=self.transfer_config_id,
            requested_time_range=self.requested_time_range,
            requested_run_time=self.requested_run_time,
            project_id=self.project_id,
            retry=self.retry,
            timeout=self.timeout,
            metadata=self.metadata,
        )

        transfer_config = _get_transfer_config_details(response.runs[0].name)
        BigQueryDataTransferConfigLink.persist(
            context=context,
            region=transfer_config["region"],
            config_id=transfer_config["config_id"],
            project_id=transfer_config["project_id"],
        )

        result = StartManualTransferRunsResponse.to_dict(response)
        run_id = get_object_id(result["runs"][0])
        context["ti"].xcom_push(key="run_id", value=run_id)

        if not self.deferrable:
            # Save as attribute for further use by OpenLineage
            self._transfer_run = self._wait_for_transfer_to_be_done(
                run_id=run_id,
                transfer_config_id=transfer_config["config_id"],
            )
            self.log.info("Transfer run %s submitted successfully.", run_id)
            return self._transfer_run

        self.defer(
            trigger=BigQueryDataTransferRunTrigger(
                project_id=self.project_id,
                config_id=transfer_config["config_id"],
                run_id=run_id,
                gcp_conn_id=self.gcp_conn_id,
                location=self.location,
                impersonation_chain=self.impersonation_chain,
            ),
            method_name="execute_completed",
        )

    def _wait_for_transfer_to_be_done(self, run_id: str, transfer_config_id: str, interval: int = 10):
        if interval <= 0:
            raise ValueError("Interval must be > 0")

        while True:
            transfer_run: TransferRun = self.hook.get_transfer_run(
                run_id=run_id,
                transfer_config_id=transfer_config_id,
                project_id=self.project_id,
                retry=self.retry,
                timeout=self.timeout,
                metadata=self.metadata,
            )
            state = transfer_run.state

            if self._job_is_done(state):
                if state in (TransferState.FAILED, TransferState.CANCELLED):
                    raise AirflowException(f"Transfer run was finished with {state} status.")

                result = TransferRun.to_dict(transfer_run)
                return result

            self.log.info("Transfer run is still working, waiting for %s seconds...", interval)
            self.log.info("Transfer run status: %s", state)
            time.sleep(interval)

    @staticmethod
    def _job_is_done(state: TransferState) -> bool:
        finished_job_statuses = [
            state.SUCCEEDED,
            state.CANCELLED,
            state.FAILED,
        ]

        return state in finished_job_statuses

    def execute_completed(self, context: Context, event: dict):
        """Execute after invoked trigger in defer method finishes its job."""
        if event["status"] in ("failed", "cancelled"):
            self.log.error("Trigger finished its work with status: %s.", event["status"])
            raise AirflowException(event["message"])

        transfer_run: TransferRun = self.hook.get_transfer_run(
            project_id=self.project_id,
            run_id=event["run_id"],
            transfer_config_id=event["config_id"],
        )

        self.log.info(
            "%s finished with message: %s",
            event["run_id"],
            event["message"],
        )

        # Save as attribute for further use by OpenLineage
        self._transfer_run = TransferRun.to_dict(transfer_run)
        return self._transfer_run

    def get_openlineage_facets_on_complete(self, _):
        """Implement _on_complete as we need a run config to extract information."""
        from urllib.parse import urlsplit

        from airflow.providers.common.compat.openlineage.facet import Dataset, ErrorMessageRunFacet
        from airflow.providers.google.cloud.hooks.gcs import _parse_gcs_url
        from airflow.providers.google.cloud.openlineage.utils import (
            BIGQUERY_NAMESPACE,
            extract_ds_name_from_gcs_path,
        )
        from airflow.providers.openlineage.extractors import OperatorLineage
        from airflow.providers.openlineage.sqlparser import DatabaseInfo, SQLParser

        if not self._transfer_run:
            self.log.debug("No BigQuery Data Transfer configuration was found by OpenLineage.")
            return OperatorLineage()

        data_source_id = self._transfer_run["data_source_id"]
        dest_dataset_id = self._transfer_run["destination_dataset_id"]
        params = self._transfer_run["params"]

        input_datasets, output_datasets = [], []
        run_facets, job_facets = {}, {}
        if data_source_id in ("google_cloud_storage", "amazon_s3", "azure_blob_storage"):
            if data_source_id == "google_cloud_storage":
                bucket, path = _parse_gcs_url(params["data_path_template"])  # gs://bucket...
                namespace = f"gs://{bucket}"
                name = extract_ds_name_from_gcs_path(path)
            elif data_source_id == "amazon_s3":
                parsed_url = urlsplit(params["data_path"])  # s3://bucket...
                namespace = f"s3://{parsed_url.netloc}"
                name = extract_ds_name_from_gcs_path(parsed_url.path)
            else:  # azure_blob_storage
                storage_account = params["storage_account"]
                container = params["container"]
                namespace = f"abfss://{container}@{storage_account}.dfs.core.windows.net"
                name = extract_ds_name_from_gcs_path(params["data_path"])

            input_datasets.append(Dataset(namespace=namespace, name=name))
            dest_table_name = params["destination_table_name_template"]
            output_datasets.append(
                Dataset(
                    namespace=BIGQUERY_NAMESPACE,
                    name=f"{self.project_id}.{dest_dataset_id}.{dest_table_name}",
                )
            )
        elif data_source_id in ("postgresql", "oracle", "mysql"):
            scheme = data_source_id if data_source_id != "postgresql" else "postgres"
            host = params["connector.endpoint.host"]
            port = params["connector.endpoint.port"]

            for asset in params["assets"]:
                # MySQL: db/table; Other: db/schema/table;
                table_name = asset.split("/")[-1]

                input_datasets.append(
                    Dataset(namespace=f"{scheme}://{host}:{int(port)}", name=asset.replace("/", "."))
                )
                output_datasets.append(
                    Dataset(
                        namespace=BIGQUERY_NAMESPACE, name=f"{self.project_id}.{dest_dataset_id}.{table_name}"
                    )
                )
        elif data_source_id == "scheduled_query":
            bq_db_info = DatabaseInfo(
                scheme="bigquery",
                authority=None,
                database=self.project_id,
            )
            parser_result = SQLParser("bigquery").generate_openlineage_metadata_from_sql(
                sql=params["query"],
                database_info=bq_db_info,
                database=self.project_id,
                use_connection=False,
                hook=None,  # Hook is not used when use_connection=False
                sqlalchemy_engine=None,
            )
            if parser_result.inputs:
                input_datasets.extend(parser_result.inputs)
            if parser_result.outputs:
                output_datasets.extend(parser_result.outputs)
            if parser_result.job_facets:
                job_facets = {**job_facets, **parser_result.job_facets}
            if parser_result.run_facets:
                run_facets = {**run_facets, **parser_result.run_facets}
            dest_table_name = params.get("destination_table_name_template")
            if dest_table_name:
                output_datasets.append(
                    Dataset(
                        namespace=BIGQUERY_NAMESPACE,
                        name=f"{self.project_id}.{dest_dataset_id}.{dest_table_name}",
                    )
                )
        else:
            self.log.debug(
                "BigQuery Data Transfer data_source_id `%s` is not supported by OpenLineage.", data_source_id
            )
            return OperatorLineage()

        error_status = self._transfer_run.get("error_status")
        if error_status and str(error_status["code"]) != "0":
            run_facets["errorMessage"] = ErrorMessageRunFacet(
                message=error_status["message"],
                programmingLanguage="python",
                stackTrace=str(error_status["details"]),
            )

        return OperatorLineage(
            inputs=input_datasets, outputs=output_datasets, job_facets=job_facets, run_facets=run_facets
        )
