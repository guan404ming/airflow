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

import glob

import pytest
from coverage import Coverage
from coverage.exceptions import NoSource


def run_tests(command_list, source, files_not_fully_covered):
    source_set = {path for item in source for path in glob.glob(item + "/**/*.py", recursive=True)}
    not_covered = {path for path in files_not_fully_covered}
    source_files = sorted(source_set)
    covered = sorted(source_set - not_covered)

    cov = Coverage(
        config_file="pyproject.toml",
        source=source,
        concurrency="multiprocessing",
    )
    with cov.collect():
        pytest.main(command_list)
    # Analyze the coverage
    failed = False
    for path in covered:
        missing_lines = cov.analysis2(path)[3]
        if len(missing_lines) > 0:
            print(f"Error: {path} has dropped in coverage. Please update tests")
            failed = True
    for path in files_not_fully_covered:
        try:
            missing_lines = cov.analysis2(path)[3]
            if not missing_lines:
                print(f"Error: {path} now has full coverage. Please remove from files_not_fully_covered")
                failed = True
        except NoSource:
            continue

    cov.combine()
    cov.html_report(morfs=source_files)
    if failed:
        print("There are some coverage errors. Please fix them")
    if len(files_not_fully_covered) > 0:
        print("Coverage run completed. Use the following commands to see the coverage report")
    print("cd htmlcov/; python -m http.server 5555")
    print("Once the server is running, open this link in your browser: http://localhost:25555")
