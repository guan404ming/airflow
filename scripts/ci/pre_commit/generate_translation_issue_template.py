#!/usr/bin/env python
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

from pathlib import Path

import yaml


def generate_translation_issue_template(json_files: list[Path]) -> dict:
    return {
        "name": "New Language Translation Checklist",
        "description": "Checklist for adding a new language translation to Airflow UI",
        "title": "New Language Translation: [LANG_CODE]",
        "labels": ["i18n", "translation"],
        "body": [
            {
                "type": "markdown",
                "attributes": {
                    "value": (
                        "## New Language Translation Checklist\n\n"
                        "Thank you for contributing a new language!\n"
                        "Please check off each file as you add its translation."
                    )
                },
            },
            {
                "type": "input",
                "id": "lang_code",
                "attributes": {
                    "label": "Language Code",
                    "description": "Please enter the language code (e.g., zh, fr, de)",
                    "placeholder": "zh",
                },
                "validations": {"required": True},
            },
            {
                "type": "checkboxes",
                "id": "translation_files",
                "attributes": {
                    "label": "Translation Files",
                    "description": "Please check each file as you complete its translation.",
                    "options": [{"label": f.name} for f in json_files],
                },
            },
        ],
    }


if __name__ == "__main__":
    EN_LOCALE_DIR = Path("airflow-core/src/airflow/ui/src/i18n/locales/en")
    ISSUE_TEMPLATE_PATH = Path(".github/ISSUE_TEMPLATE/8-translation.yml")
    json_files = sorted(EN_LOCALE_DIR.glob("*.json"))
    issue_form = generate_translation_issue_template(json_files)
    with open(ISSUE_TEMPLATE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(issue_form, f, allow_unicode=True, sort_keys=False)
    print(f"[i18n-todo] Updated {ISSUE_TEMPLATE_PATH}")
