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
from __future__ import annotations

from typing import TYPE_CHECKING

from celery.app import control

from airflow.providers.celery.version_compat import AIRFLOW_V_3_0_PLUS

if AIRFLOW_V_3_0_PLUS:
    from airflow.sdk import BaseSensorOperator
else:
    from airflow.sensors.base import BaseSensorOperator  # type: ignore[no-redef]

if TYPE_CHECKING:
    try:
        from airflow.sdk.definitions.context import Context
    except ImportError:
        # TODO: Remove once provider drops support for Airflow 2
        from airflow.utils.context import Context


class CeleryQueueSensor(BaseSensorOperator):
    """
    Waits for a Celery queue to be empty.

    By default, in order to be considered empty, the queue must not have
    any tasks in the ``reserved``, ``scheduled`` or ``active`` states.

    :param celery_queue: The name of the Celery queue to wait for.
    :param target_task_id: Task id for checking
    """

    def __init__(self, *, celery_queue: str, target_task_id: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.celery_queue = celery_queue
        self.target_task_id = target_task_id

    def _check_task_id(self, context: Context) -> bool:
        """
        Get the Celery result from the Airflow task ID and return True if the result has finished execution.

        :param context: Airflow's execution context
        :return: True if task has been executed, otherwise False
        """
        ti = context["ti"]
        celery_result = ti.xcom_pull(task_ids=self.target_task_id)
        return celery_result.ready()

    def poke(self, context: Context) -> bool:
        if self.target_task_id:
            return self._check_task_id(context)

        inspect_result = control.Inspect()
        reserved = inspect_result.reserved()
        scheduled = inspect_result.scheduled()
        active = inspect_result.active()

        try:
            reserved = len(reserved[self.celery_queue])
            scheduled = len(scheduled[self.celery_queue])
            active = len(active[self.celery_queue])

            self.log.info("Checking if celery queue %s is empty.", self.celery_queue)

            return reserved == 0 and scheduled == 0 and active == 0
        except KeyError:
            message = f"Could not locate Celery queue {self.celery_queue}"
            raise KeyError(message)
