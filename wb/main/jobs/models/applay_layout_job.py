"""
 OpenVINO DL Workbench
 Class for job to apply layout to a model

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
from contextlib import closing
from defusedxml import ElementTree

from openvino.runtime import Core, Layout
from openvino.runtime.passes import Manager
from openvino.preprocess import PrePostProcessor
from sqlalchemy.orm import Session

from wb.extensions_factories.database import get_db_session_for_celery
from wb.main.enumerates import JobTypesEnum, StatusEnum
from wb.main.jobs.interfaces.ijob import IJob
from wb.main.models.apply_model_layout_model import ApplyModelLayoutJobModel
from wb.main.utils.utils import find_by_ext


class ApplyModelLayoutJob(IJob):
    job_type = JobTypesEnum.apply_model_layout
    _job_model_class = ApplyModelLayoutJobModel

    def __init__(self, job_id: int, **unused_args):
        super().__init__(job_id=job_id)
        self._attach_default_db_and_socket_observers()

    def run(self):
        self._job_state_subject.update_state(status=StatusEnum.running, progress=0,
                                             log='Starting model layout applying DevCloud annotate dataset result job')
        with closing(get_db_session_for_celery()) as session:
            session: Session
            job_model: ApplyModelLayoutJobModel = self.get_job_model(session=session)
            layout = job_model.layout
            model = job_model.model
            model_file_path = find_by_ext(model.path, 'xml')
            weights_file_path = find_by_ext(model.path, 'bin')
        self._job_state_subject.update_state(status=StatusEnum.running, progress=20)
        self._apply_model_layout(model_file_path, weights_file_path, layout)
        self.on_success()

    def _apply_model_layout(self, model_path: str, weights_path: str, layout_config: dict):
        core = Core()
        model = core.read_model(model_path, weights_path)

        pre_processing = PrePostProcessor(model)

        for input_config in layout_config:
            index = input_config['index']
            layout_list = input_config['layout']
            layout_str = ''.join(layout_list)
            layout = Layout(layout_str)
            pre_processing.input(index).model().set_layout(layout)

        self._job_state_subject.update_state(status=StatusEnum.running, progress=40)

        pre_processing.build()

        old_model_content = ElementTree.parse(model_path)
        metadata = old_model_content.find('./meta_data')

        pass_manager = Manager()
        pass_manager.register_pass('Serialize', model_path, weights_path)
        pass_manager.run_passes(model)

        if metadata:
            new_model_content = ElementTree.parse(model_path)
            new_model_content.getroot().append(metadata)
            new_model_content.write(model_path)

        self._job_state_subject.update_state(status=StatusEnum.running, progress=60)

    def on_success(self):
        self._job_state_subject.update_state(status=StatusEnum.ready,
                                             log='Apply model layout job successfully finished',
                                             progress=100)
        self._job_state_subject.detach_all_observers()
