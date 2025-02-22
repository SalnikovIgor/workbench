"""
 OpenVINO DL Workbench
 Base abstractions for creation environment

 Copyright (c) 2021 Intel Corporation

 LEGAL NOTICE: Your use of this software and any required dependent software (the “Software Package”) is subject to
 the terms and conditions of the software license agreements for Software Package, which may also include
 notices, disclaimers, or license terms for third party or open source software
 included in or with the Software Package, and your use indicates your acceptance of all such terms.
 Please refer to the “third-party-programs.txt” or other similarly-named text file included with the Software Package
 for additional details.
 You may obtain a copy of the License at
      https://software.intel.com/content/dam/develop/external/us/en/documents/intel-openvino-license-agreements.pdf
"""
from pathlib import Path
from typing import List

import pkg_resources
from sqlalchemy.orm import Session

from wb.main.console_tool_wrapper.environment_managment_tool import CollectInstalledPackagesTool
from wb.main.environment.manifest import Manifest
from wb.main.jobs.tools_runner.local_runner import LocalRunner
from wb.main.models import EnvironmentModel, DependencyModel


class EnvironmentCreator:
    """Base abstract class for creating environment"""

    def __init__(self, manifest: Manifest, status_report_callback):
        super().__init__()
        self._manifest = manifest
        self._status_report_callback = status_report_callback

    def create(self, session: Session, is_prc: bool) -> EnvironmentModel:
        environment = self._create(session, is_prc)
        self._save_installed_packages_to_environment(environment, session)
        return environment

    def _create(self, session: Session, is_prc: bool) -> EnvironmentModel:
        raise NotImplementedError(f'create method is not implemented in {self.__class__}')

    @staticmethod
    def _save_installed_packages_to_environment(environment: EnvironmentModel, session: Session):
        installed_packages = EnvironmentCreator._collect_installed_packages(environment)
        EnvironmentCreator._save_dependencies(installed_packages, environment, session)

    @staticmethod
    def _collect_installed_packages(environment: EnvironmentModel):
        tool = CollectInstalledPackagesTool(python_exec=environment.python_executable)
        runner = LocalRunner(tool=tool)
        exit_code, output = runner.run_console_tool()
        if exit_code:
            raise RuntimeError(f'Cannot collect installed packages from {environment.path}]')
        output_lines = output.splitlines()
        packages = EnvironmentCreator.filter_packages(output_lines)
        packages_path = Path(environment.path) / 'packages.txt'
        with packages_path.open('w') as packages_file:
            packages_file.write(packages)
        with packages_path.open() as packages_file:
            return list(pkg_resources.parse_requirements(packages_file))

    @staticmethod
    def filter_packages(packages: List[str]) -> str:
        result_packages = []
        for package in packages:
            if not package:
                continue
            try:
                pkg_resources.Requirement.parse(package)
            except pkg_resources.RequirementParseError:
                continue
            result_packages.append(package)
        return '\n'.join(result_packages)

    @staticmethod
    def _save_dependencies(dependencies: List, environment: EnvironmentModel, session: Session):
        for dependency in dependencies:
            package_name = dependency.name
            # TODO: extract
            if package_name in ('openvino', 'openvino-dev'):
                version = '2022.1.0'
            else:
                version = dependency.specs[0][1]
            dependency = DependencyModel(package=package_name, version=version,
                                         environment_id=environment.id)
            dependency.write_record(session)
