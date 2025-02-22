"""
 OpenVINO DL Workbench
 Class for local accuracy job

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
from sqlalchemy.orm import Session

from config.constants import OPENVINO_ROOT_PATH
from wb.main.enumerates import JobTypesEnum
from wb.main.jobs.accuracy_analysis.accuracy.accuracy_job import AccuracyJob
from wb.main.jupyter_notebooks.update_jupyter_notebook_decorator import update_jupyter_notebook_job
from wb.main.models import AccuracyJobsModel


# TODO Consider renaming class to CreateAccuracyReportJob
@update_jupyter_notebook_job
class LocalAccuracyJob(AccuracyJob):
    job_type = JobTypesEnum.accuracy_type

    def _set_paths(self, session: Session):
        """
        Set job paths for local and remote use-cases.
        This method mutates `job_bundle_path`, `_openvino_path` and `_venv_path` fields
        """
        accuracy_job_model: AccuracyJobsModel = self.get_job_model(session)
        self.job_bundle_path = str(self.get_accuracy_artifacts_path(accuracy_job_model))
        self._openvino_path = OPENVINO_ROOT_PATH
        self._venv_path = None

    def collect_artifacts(self):
        pass
