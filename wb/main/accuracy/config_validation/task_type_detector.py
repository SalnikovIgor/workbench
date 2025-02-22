"""
 OpenVINO DL Workbench
 Task type detector

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
from typing import Tuple

from wb.main.enumerates import TaskMethodEnum
from wb.main.shared.enumerates import TaskEnum

ADAPTER_TYPE_TO_TASK_MAP = {
    'bert_classification': TaskEnum.classification,
    'class_agnostic_detection': TaskEnum.object_detection,
    'classification': TaskEnum.classification,
    'ctdet': TaskEnum.object_detection,
    'face_detection': TaskEnum.object_detection,
    'face_detection_refinement': TaskEnum.object_detection,
    'faceboxes': TaskEnum.object_detection,
    'faster_rcnn_onnx': TaskEnum.object_detection,
    'head_detection': TaskEnum.object_detection,
    'inpainting': TaskEnum.inpainting,
    'landmarks_regression': TaskEnum.landmark_detection,
    'mask_rcnn': TaskEnum.instance_segmentation,
    'person_vehicle_detection': TaskEnum.object_detection,
    'person_vehilce_detection_refinement': TaskEnum.object_detection,
    'pytorch_ssd_decoder': TaskEnum.object_detection,
    'reid': TaskEnum.face_recognition,
    'segmentation': TaskEnum.semantic_segmentation,
    'segmentation_one_class': TaskEnum.semantic_segmentation,
    'ssd': TaskEnum.object_detection,
    'ssd_mxnet': TaskEnum.object_detection,
    'ssd_onnx': TaskEnum.object_detection,
    'style_transfer': TaskEnum.style_transfer,
    'super_resolution': TaskEnum.super_resolution,
    'super_resolution_yuv': TaskEnum.super_resolution,
    'tf_object_detection': TaskEnum.object_detection,
    'tiny_yolo_v1': TaskEnum.object_detection,
    'two_stage_detection': TaskEnum.object_detection,
    'yolo_v2': TaskEnum.object_detection,
    'yolo_v3': TaskEnum.object_detection,
    'yolo_v3_onnx': TaskEnum.object_detection,
}


ADAPTER_TYPE_TO_TASK_METHOD_MAP = {
    'classification': TaskMethodEnum.classificator,
    'inpainting': TaskMethodEnum.inpainting,
    'landmarks_regression': TaskEnum.landmark_detection,
    'mask_rcnn': TaskMethodEnum.mask_rcnn,
    'reid': TaskMethodEnum.face_recognition,
    'segmentation': TaskMethodEnum.segmentation,
    'ssd': TaskMethodEnum.ssd,
    'style_transfer': TaskMethodEnum.style_transfer,
    'super_resolution': TaskMethodEnum.super_resolution,
    'yolo_v2': TaskMethodEnum.yolo_v2,
    'yolo_v3': TaskMethodEnum.yolo_v3,
}


def detect_types(adapter_type: str) -> Tuple[TaskEnum, TaskMethodEnum]:
    """
    Detects TaskEnum and TaskMethodEnum by accuracy checker adapter type
    :param adapter_type: accuracy checker adapter type
    """
    task_type: TaskEnum = ADAPTER_TYPE_TO_TASK_MAP.get(adapter_type, TaskEnum.custom)
    task_method: TaskMethodEnum = ADAPTER_TYPE_TO_TASK_METHOD_MAP.get(adapter_type, TaskMethodEnum.custom)

    return task_type, task_method
