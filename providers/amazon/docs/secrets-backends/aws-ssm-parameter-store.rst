 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

.. _ssm_parameter_store_secrets:

AWS SSM Parameter Store Secrets Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enable SSM parameter store, specify :py:class:`~airflow.providers.amazon.aws.secrets.systems_manager.SystemsManagerParameterStoreBackend`
as the ``backend`` in  ``[secrets]`` section of ``airflow.cfg``.

Here is a sample configuration:

.. code-block:: ini

    [secrets]
    backend = airflow.providers.amazon.aws.secrets.systems_manager.SystemsManagerParameterStoreBackend
    backend_kwargs = {
      "connections_prefix": "airflow/connections",
      "connections_lookup_pattern": null,
      "variables_prefix": "airflow/variables",
      "variables_lookup_pattern": null,
      "config_prefix": "airflow/config",
      "config_lookup_pattern": null,
      "profile_name": "default"
    }

To authenticate you can either supply arguments listed in
:ref:`Amazon Webservices Connection Extra config <howto/connection:aws:configuring-the-connection>` or set
`environment variables <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables>`__.

.. code-block:: ini

    [secrets]
    backend = airflow.providers.amazon.aws.secrets.systems_manager.SystemsManagerParameterStoreBackend
    backend_kwargs = {
      "connections_prefix": "airflow/connections",
      "variables_prefix": "airflow/variables",
      "config_prefix": "airflow/config",
      "role_arn": "arn:aws:iam::123456789098:role/role-name"
    }


Optional lookup
"""""""""""""""

Optionally connections, variables, or config may be looked up exclusive of each other or in any combination.
This will prevent requests being sent to AWS SSM Parameter Store for the excluded type.

If you want to look up some and not others in AWS SSM Parameter Store you may do so by setting the relevant ``*_prefix`` parameter of the ones to be excluded as ``null``.

For example, if you want to set parameter ``connections_prefix`` to ``"airflow/connections"`` and not look up variables and config, your configuration file should look like this:

.. code-block:: ini

    [secrets]
    backend = airflow.providers.amazon.aws.secrets.systems_manager.SystemsManagerParameterStoreBackend
    backend_kwargs = {
      "connections_prefix": "airflow/connections",
      "variables_prefix": null,
      "config_prefix": null,
      "profile_name": "default"
    }

If you want to only lookup a specific subset of connections, variables or config in AWS Secrets Manager, you may do so by setting the relevant ``*_lookup_pattern`` parameter.
This parameter takes a Regex as a string as value.

For example, if you want to only lookup connections starting by "m" in AWS Secrets Manager, your configuration file should look like this:

.. code-block:: ini

    [secrets]
    backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
    backend_kwargs = {
      "connections_prefix": "airflow/connections",
      "connections_lookup_pattern": "^m",
      "profile_name": "default"
    }

Storing and Retrieving Connections
""""""""""""""""""""""""""""""""""

If you have set ``connections_prefix`` as ``/airflow/connections``, then for a connection id of ``smtp_default``,
you would want to store your connection at ``/airflow/connections/smtp_default``.

Optionally you can supply a profile name to reference aws profile, e.g. defined in ``~/.aws/config``.

The value of the SSM parameter must be the :ref:`connection URI representation <generating_connection_uri>`
or in the :ref:`JSON Format <connection-serialization-json-example>` of the connection object.

In some cases, URI's that you will need to store in AWS SSM Parameter Store may not be intuitive,
for example when using HTTP / HTTPS or SPARK, you may need URI's that will look like this:

.. code-block:: ini

    http://https%3A%2F%2Fexample.com

    spark://spark%3A%2F%2Fspark-main-0.spark-main.spark:7077

This is a known situation, where schema and protocol parts of the URI are independent and in some cases, need to be specified explicitly.

See GitHub issue `#10256 <https://github.com/apache/airflow/pull/10256>`__
and `#10913 <https://github.com/apache/airflow/issues/10913>`__ for more detailed discussion that led to this documentation update.
This may get resolved in the future.


The same connections could be represented in AWS SSM Parameter Store as a JSON Object

.. code-block:: json

    {"conn_type": "http", "host": "https://example.com"}

    {"conn_type": "spark", "host": "spark://spark-main-0.spark-main.spark", "port": 7077}


Storing and Retrieving Variables
""""""""""""""""""""""""""""""""

If you have set ``variables_prefix`` as ``/airflow/variables``, then for an Variable key of ``hello``,
you would want to store your Variable at ``/airflow/variables/hello``.

Optionally you can supply a profile name to reference aws profile, e.g. defined in ``~/.aws/config``.
