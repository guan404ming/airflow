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

# NOTE! THIS FILE IS AUTOMATICALLY GENERATED AND WILL BE OVERWRITTEN!
#
# IF YOU WANT TO MODIFY THIS FILE, YOU SHOULD MODIFY THE TEMPLATE
# `get_provider_info_TEMPLATE.py.jinja2` IN the `dev/breeze/src/airflow_breeze/templates` DIRECTORY


def get_provider_info():
    return {
        "package-name": "apache-airflow-providers-elasticsearch",
        "name": "Elasticsearch",
        "description": "`Elasticsearch <https://www.elastic.co/elasticsearch>`__\n",
        "integrations": [
            {
                "integration-name": "Elasticsearch",
                "external-doc-url": "https://www.elastic.co/elasticsearch",
                "logo": "/docs/integration-logos/Elasticsearch.png",
                "tags": ["software"],
            }
        ],
        "hooks": [
            {
                "integration-name": "Elasticsearch",
                "python-modules": ["airflow.providers.elasticsearch.hooks.elasticsearch"],
            }
        ],
        "connection-types": [
            {
                "hook-class-name": "airflow.providers.elasticsearch.hooks.elasticsearch.ElasticsearchSQLHook",
                "connection-type": "elasticsearch",
            }
        ],
        "logging": ["airflow.providers.elasticsearch.log.es_task_handler.ElasticsearchTaskHandler"],
        "config": {
            "elasticsearch": {
                "description": None,
                "options": {
                    "host": {
                        "description": "Elasticsearch host\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "default": "",
                    },
                    "log_id_template": {
                        "description": "Format of the log_id, which is used to query for a given tasks logs\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "is_template": True,
                        "default": "{dag_id}-{task_id}-{run_id}-{map_index}-{try_number}",
                    },
                    "end_of_log_mark": {
                        "description": "Used to mark the end of a log stream for a task\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "default": "end_of_log",
                    },
                    "frontend": {
                        "description": "Qualified URL for an elasticsearch frontend (like Kibana) with a template argument for log_id\nCode will construct log_id using the log_id template from the argument above.\nNOTE: scheme will default to https if one is not provided\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": "http://localhost:5601/app/kibana#/discover?_a=(columns:!(message),query:(language:kuery,query:'log_id: \"{log_id}\"'),sort:!(log.offset,asc))",
                        "default": "",
                    },
                    "write_stdout": {
                        "description": "Write the task logs to the stdout of the worker, rather than the default files\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "default": "False",
                    },
                    "write_to_es": {
                        "description": "Write the task logs to the ElasticSearch\n",
                        "version_added": "5.5.4",
                        "type": "string",
                        "example": None,
                        "default": "False",
                    },
                    "target_index": {
                        "description": "Name of the index to write to, when enabling writing the task logs to the ElasticSearch\n",
                        "version_added": "5.5.4",
                        "type": "string",
                        "example": None,
                        "default": "airflow-logs",
                    },
                    "json_format": {
                        "description": "Instead of the default log formatter, write the log lines as JSON\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "default": "False",
                    },
                    "json_fields": {
                        "description": "Log fields to also attach to the json output, if enabled\n",
                        "version_added": "1.10.4",
                        "type": "string",
                        "example": None,
                        "default": "asctime, filename, lineno, levelname, message",
                    },
                    "host_field": {
                        "description": "The field where host name is stored (normally either `host` or `host.name`)\n",
                        "version_added": "2.1.1",
                        "type": "string",
                        "example": None,
                        "default": "host",
                    },
                    "offset_field": {
                        "description": "The field where offset is stored (normally either `offset` or `log.offset`)\n",
                        "version_added": "2.1.1",
                        "type": "string",
                        "example": None,
                        "default": "offset",
                    },
                    "index_patterns": {
                        "description": "Comma separated list of index patterns to use when searching for logs (default: `_all`).\nThe index_patterns_callable takes precedence over this.\n",
                        "version_added": "2.6.0",
                        "type": "string",
                        "example": "something-*",
                        "default": "_all",
                    },
                    "index_patterns_callable": {
                        "description": "A string representing the full path to the Python callable path which accept TI object and\nreturn comma separated list of index patterns. This will takes precedence over index_patterns.\n",
                        "version_added": "5.5.0",
                        "type": "string",
                        "example": "module.callable",
                        "default": "",
                    },
                },
            },
            "elasticsearch_configs": {
                "description": None,
                "options": {
                    "http_compress": {
                        "description": None,
                        "version_added": "1.10.5",
                        "type": "string",
                        "example": None,
                        "default": "False",
                    },
                    "verify_certs": {
                        "description": None,
                        "version_added": "1.10.5",
                        "type": "string",
                        "example": None,
                        "default": "True",
                    },
                },
            },
        },
    }
