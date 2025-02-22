"""
 OpenVINO DL Workbench
 Class for parsing DevCloud accuracy result job

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
import logging as log
import shutil
import tarfile
from contextlib import closing
from pathlib import Path
from typing import List
from sqlalchemy.orm import Session

from config.constants import ACCURACY_ARTIFACTS_FOLDER, ACCURACY_RESULT_FILE_NAME
from wb.error.job_error import ManualTaskRetryException
from wb.extensions_factories.database import get_db_session_for_celery
from wb.main.accuracy_report.accuracy_result_processor import AccuracyResultProcessor
from wb.main.jobs.accuracy_analysis.accuracy.accuracy_job_state import AccuracyJobStateSubject
from wb.main.jobs.interfaces.ijob import IJob
from wb.main.jobs.interfaces.job_observers import ParseDevCloudResultDBObserver
from wb.main.enumerates import JobTypesEnum, AccuracyReportTypeEnum, StatusEnum
from wb.main.models import (AccuracyJobsModel, ProjectsModel, DatasetsModel, DownloadableArtifactsModel,
                            ParseDevCloudAccuracyResultJobModel)
from wb.main.scripts.accuracy_tool.tool_output import AccuracyResult, AcCLIOutput
from wb.main.utils.utils import create_empty_dir


class ParseDevCloudAccuracyResultJob(IJob):
    job_type = JobTypesEnum.parse_dev_cloud_accuracy_result_job
    _job_model_class = ParseDevCloudAccuracyResultJobModel
    _job_state_subject: AccuracyJobStateSubject

    def __init__(self, job_id: int, **unused_kwargs):
        super().__init__(job_id=job_id)
        self._job_state_subject = AccuracyJobStateSubject(self._job_id)
        database_observer = ParseDevCloudResultDBObserver(job_id=self._job_id)
        self._job_state_subject.attach(database_observer)
        self._attach_default_db_and_socket_observers()

    def run(self):
        self._job_state_subject.update_state(status=StatusEnum.running, progress=0,
                                             log='Starting parse DevCloud accuracy result job')
        with closing(get_db_session_for_celery()) as session:
            session: Session
            parse_accuracy_result_job_model: ParseDevCloudAccuracyResultJobModel = self.get_job_model(session)
            accuracy_job_model: AccuracyJobsModel = next(
                filter(
                    lambda job: job.job_type == JobTypesEnum.accuracy_type.value,
                    parse_accuracy_result_job_model.pipeline.jobs
                )
            )

            project: ProjectsModel = accuracy_job_model.project
            project_id = project.id
            target_dataset: DatasetsModel = accuracy_job_model.target_dataset
            target_dataset_id = target_dataset.id
            accuracy_report_type = accuracy_job_model.accuracy_report_type

            result_artifact: DownloadableArtifactsModel = parse_accuracy_result_job_model.result_artifact
            if not result_artifact.is_all_files_uploaded:
                raise ManualTaskRetryException('Accuracy result artifact is not uploaded yet, retry task')

            artifact_path = result_artifact.files[0].path
            result_artifacts_path = Path(ACCURACY_ARTIFACTS_FOLDER) / str(parse_accuracy_result_job_model.pipeline_id)

        log.debug('Parsing accuracy result artifact and saving data to database')
        self._extract_accuracy_results(artifact_path, result_artifacts_path)
        self._process_accuracy_results(accuracy_report_type, project_id, result_artifacts_path, target_dataset_id)
        self.on_success()

    @staticmethod
    def _extract_accuracy_results(archive_path: str, destination_path: Path):
        create_empty_dir(destination_path)
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(destination_path)

    def on_success(self):
        self._job_state_subject.update_state(status=StatusEnum.ready,
                                             log='Parse DevCloud accuracy result job successfully finished')
        self._job_state_subject.detach_all_observers()

    def _process_accuracy_results(self, accuracy_report_type: AccuracyReportTypeEnum,
                                  project_id: int, accuracy_report_dir: Path, target_dataset_id: int):
        results: List[AccuracyResult] = self._parse_ac_results(accuracy_report_dir)

        AccuracyResultProcessor(
            report_type=accuracy_report_type,
            accuracy_report_dir=accuracy_report_dir,
            project_id=project_id,
            target_dataset_id=target_dataset_id
        ).process_results(results)

        if accuracy_report_dir.exists():
            shutil.rmtree(accuracy_report_dir)

    @staticmethod
    def _parse_ac_results(accuracy_report_dir: Path) -> List[AccuracyResult]:
        accuracy_results_file_path = accuracy_report_dir / ACCURACY_RESULT_FILE_NAME
        with accuracy_results_file_path.open() as accuracy_results_file:
            accuracy_results = accuracy_results_file.readline()
        ac_output = AcCLIOutput.from_string(accuracy_results)
        return ac_output.accuracy_results
