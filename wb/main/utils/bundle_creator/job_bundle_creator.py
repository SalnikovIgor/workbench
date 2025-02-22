"""
 OpenVINO DL Workbench
 Class for managing of deploy bundle

 Copyright (c) 2018 Intel Corporation

 LEGAL NOTICE: Your use of this software and any required dependent software (the “Software Package”) is subject to
 the terms and conditions of the software license agreements for Software Package, which may also include
 notices, disclaimers, or license terms for third party or open source software
 included in or with the Software Package, and your use indicates your acceptance of all such terms.
 Please refer to the “third-party-programs.txt” or other similarly-named text file included with the Software Package
 for additional details.
 You may obtain a copy of the License at
      https://software.intel.com/content/dam/develop/external/us/en/documents/intel-openvino-license-agreements.pdf
"""
import os
import shutil
import tempfile

from wb.main.utils.bundle_creator.bundle_creator import BundleComponent, BundleCreator, ComponentsParams
from wb.main.utils.utils import get_size_of_files
from config.constants import (JOBS_SCRIPTS_FOLDER, ROOT_FOLDER, JOBS_SCRIPTS_FOLDER_NAME,
                              PROFILING_JOB_WRAPPER_NAME, SHARED_MODULE_FOLDER, SHARED_MODULE_FOLDER_NAME,
                              DATASET_ANNOTATOR_LOCAL_SCRIPT_PATH, DATASET_ANNOTATOR_FOLDER_NAME)


class JobComponentsParams(ComponentsParams):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.components = self._build_components(*args, **kwargs)

    def _build_components(self, model_path: str, dataset_path: str,
                          job_run_script: str, config_file: str, **kwargs) -> dict:
        return {
            'model': self._create_model_component(model_path),
            'dataset': self._create_dataset_component(dataset_path),
            'job_run_script': self._create_job_run_component(job_run_script=job_run_script,
                                                             config_file=config_file,
                                                             **kwargs)
        }

    @staticmethod
    def _create_model_component(model_path: str) -> dict:
        return {
            'enabled': True,
            'component': BundleComponent(model_path, 'model')
        }

    @staticmethod
    def _create_dataset_component(dataset_path) -> dict:
        return {
            'enabled': True,
            'component': BundleComponent(dataset_path, 'dataset')
        }

    def _create_job_run_component(self, job_run_script, config_file, **kwargs) -> dict:
        return {
            'enabled': True,
            'component': self.create_job_run_script_component(job_run_script, config_file, **kwargs)
        }

    @staticmethod
    def create_job_run_script_component(job_run_script: str, config_file: str, **unused_kwargs) -> BundleComponent:
        dependencies = (
            BundleComponent(config_file, JOBS_SCRIPTS_FOLDER_NAME),
        )
        return BundleComponent(job_run_script, JOBS_SCRIPTS_FOLDER_NAME, executable=True, dependencies=dependencies)


class ProfilingComponentsParams(JobComponentsParams):
    def __init__(self, model_path: str, dataset_path: str,
                 job_run_script: str, config_file: str):
        report_reader_file = os.path.join(ROOT_FOLDER,
                                          'wb',
                                          'utils',
                                          'benchmark_report',
                                          'benchmark_report.py')

        super().__init__(model_path=model_path, dataset_path=dataset_path,
                         job_run_script=job_run_script, config_file=config_file,
                         report_reader=report_reader_file)

    @staticmethod
    def create_job_run_script_component(job_run_script: str, config_file: str, **kwargs) -> BundleComponent:
        dependencies = (
            BundleComponent(os.path.join(JOBS_SCRIPTS_FOLDER, PROFILING_JOB_WRAPPER_NAME), JOBS_SCRIPTS_FOLDER_NAME),
            BundleComponent(config_file, JOBS_SCRIPTS_FOLDER_NAME),
            BundleComponent(kwargs['report_reader'], JOBS_SCRIPTS_FOLDER_NAME)
        )
        return BundleComponent(job_run_script, JOBS_SCRIPTS_FOLDER_NAME, executable=True, dependencies=dependencies)


class AccuracyComponentsParams(JobComponentsParams):
    def __init__(self, model_path: str, dataset_path: str,
                 job_run_script: str, config_file: str):
        super().__init__(model_path=model_path, dataset_path=dataset_path,
                         job_run_script=job_run_script, config_file=config_file)

    @staticmethod
    def create_job_run_script_component(job_run_script: str, config_file: str, **unused_kwargs) -> BundleComponent:
        dependencies = (
            BundleComponent(os.path.join(JOBS_SCRIPTS_FOLDER, 'accuracy_tool'),
                            os.path.join(JOBS_SCRIPTS_FOLDER_NAME, 'accuracy_tool')),
            BundleComponent(config_file, JOBS_SCRIPTS_FOLDER_NAME),
        )
        return BundleComponent(job_run_script, JOBS_SCRIPTS_FOLDER_NAME, executable=True, dependencies=dependencies)


class PerTensorDistanceComponentsParams(JobComponentsParams):
    def _build_components(self, parent_model_path, optimized_model_path, dataset_path,
                          job_run_script, *args, **kwargs) -> dict:
        return {
            'models': {
                'enabled': True,
                'component': self._build_models_component(parent_model_path=parent_model_path,
                                                          optimized_model_path=optimized_model_path)
            },
            'dataset': self._create_dataset_component(dataset_path),
            'job_run_script': {
                'enabled': True,
                'component': self.create_job_run_script_component(job_run_script, **kwargs)
            }
        }

    @staticmethod
    def _build_models_component(parent_model_path, optimized_model_path) -> BundleComponent:
        parent_model_component = BundleComponent(parent_model_path, 'models/parent')
        return BundleComponent(optimized_model_path, 'models/optimized', dependencies=(parent_model_component,))

    @staticmethod
    def create_job_run_script_component(job_run_script: str, **unused_kwargs) -> BundleComponent:
        dependencies = (
            BundleComponent(os.path.join(JOBS_SCRIPTS_FOLDER, 'calculate_tensor_distance.py'),
                            JOBS_SCRIPTS_FOLDER_NAME),
            BundleComponent(SHARED_MODULE_FOLDER,
                            os.path.join(JOBS_SCRIPTS_FOLDER_NAME, SHARED_MODULE_FOLDER_NAME)),
        )
        return BundleComponent(job_run_script, JOBS_SCRIPTS_FOLDER_NAME, executable=True, dependencies=dependencies)


class AnnotateDatasetComponentsParams(JobComponentsParams):
    def __init__(self, model_path: str, dataset_path: str,
                 job_run_script: str, config_file: str):
        super().__init__(model_path=model_path, dataset_path=dataset_path,
                         job_run_script=job_run_script, config_file=config_file)

    @staticmethod
    def create_job_run_script_component(job_run_script: str, config_file: str, **unused_kwargs) -> BundleComponent:
        dependencies = (
            BundleComponent(DATASET_ANNOTATOR_LOCAL_SCRIPT_PATH,
                            os.path.join(JOBS_SCRIPTS_FOLDER_NAME, DATASET_ANNOTATOR_FOLDER_NAME)),
            BundleComponent(SHARED_MODULE_FOLDER,
                            os.path.join(JOBS_SCRIPTS_FOLDER_NAME, DATASET_ANNOTATOR_FOLDER_NAME,
                                         SHARED_MODULE_FOLDER_NAME)),
            BundleComponent(config_file, JOBS_SCRIPTS_FOLDER_NAME),
        )
        return BundleComponent(job_run_script, JOBS_SCRIPTS_FOLDER_NAME, executable=True, dependencies=dependencies)


class JobBundleCreator(BundleCreator):
    def create(self, components: ComponentsParams,
               destination_bundle: str) -> str:
        with tempfile.TemporaryDirectory() as tmpdirname:
            full_size = 0
            for dependency in components.get_components():
                full_size += get_size_of_files(dependency.source_path)
            for dependency in components.get_components():
                dep_size = get_size_of_files(dependency.source_path)
                progress_per_component = dep_size / full_size * 100
                self.log(f'Copying dependency {dependency.source_path}')
                self._copy_component(dependency, root_bundle_path=tmpdirname)
                self.log(f'Copying dependency {dependency.source_path} - done',
                         progress_increase=progress_per_component)
            destination_bundle_path = os.path.dirname(destination_bundle)
            if not os.path.exists(destination_bundle_path):
                os.makedirs(destination_bundle_path)
            bundle_archive_path = shutil.make_archive(
                base_name=destination_bundle,
                root_dir=tmpdirname, format='gztar')
            self.log(f'Bundle archive created in {destination_bundle}', progress_increase=30)
            return bundle_archive_path
