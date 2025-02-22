"""
 OpenVINO DL Workbench
 Endpoints to work with hf

 Copyright (c) 2022 Intel Corporation

 LEGAL NOTICE: Your use of this software and any required dependent software (the “Software Package”) is subject to
 the terms and conditions of the software license agreements for Software Package, which may also include
 notices, disclaimers, or license terms for third party or open source software
 included in or with the Software Package, and your use indicates your acceptance of all such terms.
 Please refer to the “third-party-programs.txt” or other similarly-named text file included with the Software Package
 for additional details.
 You may obtain a copy of the License at
      https://software.intel.com/content/dam/develop/external/us/en/documents/intel-openvino-license-agreements.pdf
"""
from collections import Counter
from pathlib import Path
from typing import List, Optional

from huggingface_hub import HfApi, hf_hub_url
from huggingface_hub.file_download import cached_download
from huggingface_hub.hf_api import ModelInfo
from transformers.onnx import FeaturesManager

_huggingface_api = HfApi()


class HuggingfaceModelConfig:
    def __init__(
            self,
            architectures: Optional[List[str]] = None,
            model_type: Optional[str] = None,
            **kwargs,
    ):
        self.architectures = architectures
        self.model_type = model_type

    def json(self):
        return {
            'architectures': self.architectures,
            'modelType': self.model_type,
        }


class ValidationResult:
    def __init__(self, disabled: bool, message: Optional[str] = None):
        self.disabled = disabled
        self.message = message

    def json(self) -> dict:
        result = {'disabled': self.disabled}
        if self.message:
            result['message'] = self.message
        return result


class HuggingfaceModel:
    def __init__(
            self,
            model_id: str,
            pipeline_tag: str,
            last_modified: str,
            tags: List[str],
            validation: ValidationResult,
            siblings: Optional[List[str]] = None,
            config: Optional[dict] = None,
            downloads: Optional[int] = None,
    ):
        self.model_id = model_id
        self.pipeline_tag = pipeline_tag
        self.last_modified = last_modified
        self.tags = tags
        self.validation = validation
        self.siblings = siblings
        self.config = HuggingfaceModelConfig(**config) if config else None
        self.downloads = downloads

    def json(self):
        return {
            'id': self.model_id,
            'pipelineTag': self.pipeline_tag,
            'lastModified': self.last_modified,
            'tags': self.tags,
            'validation': self.validation.json(),
            'siblings': self.siblings,
            'config': self.config.json() if self.config else None,
            'downloads': self.downloads,
        }


def _validate_hf_model(model: ModelInfo) -> ValidationResult:
    if not model.config:
        return ValidationResult(disabled=True, message='Model has no config')
    if 'model_type' not in model.config.keys():
        return ValidationResult(disabled=True, message='Model has no model type')
    model_type = model.config['model_type']
    if model_type not in FeaturesManager._SUPPORTED_MODEL_TYPE:
        return ValidationResult(disabled=True, message=f'Model type {model_type} is not supported')
    if 'sequence-classification' not in FeaturesManager._SUPPORTED_MODEL_TYPE[model_type]:
        return ValidationResult(
            disabled=True,
            message=f'Sequence classification feature is not supported for model type {model_type}'
        )
    return ValidationResult(disabled=False)


def _convert_hf_model_info(model_info: ModelInfo) -> HuggingfaceModel:
    return HuggingfaceModel(
        model_id=model_info.modelId,
        pipeline_tag=model_info.pipeline_tag,
        last_modified=model_info.lastModified,
        tags=model_info.tags,
        validation=_validate_hf_model(model_info),
        siblings=[x.rfilename for x in model_info.siblings],
        config=model_info.config,
        downloads=getattr(model_info, 'downloads', None),
    )


def get_model_type_filter_options(models: List[HuggingfaceModel]) -> List[str]:
    counter = Counter()
    for model in models:
        if not model.config or not model.config.model_type:
            continue
        counter[model.config.model_type] += 1
    return [model_type for model_type, _ in counter.most_common()]


# todo: 81020, parallel models and tags requests once mechanism implemented
def get_models() -> dict:
    pipeline_tag = 'text-classification'
    applied_tags = {
        'pipelineTags': [pipeline_tag],
        'libraries': ['pytorch', 'transformers'],
    }
    models = _huggingface_api.list_models(
        filter=[tags for tags_list in applied_tags.values() for tags in tags_list],
        sort='downloads',
        direction=-1,
        fetch_config=True
    )
    models = [_convert_hf_model_info(model) for model in models if model.pipeline_tag == pipeline_tag]
    return {
        'models': [model.json() for model in models],
        'tags': {
            'applied': applied_tags,
            'available': {
                'modelTypes': get_model_type_filter_options(models)
            }
        },
    }


def get_tags() -> dict:
    tags = _huggingface_api.get_model_tags()
    return {
        'languages': list(tags.language.values()),
        'licenses': list(tags.license.values()),
    }


def get_model_details(model_id: str) -> Path:
    hf_readme_url = hf_hub_url(repo_id=model_id, filename="README.md")
    readme_path = Path(cached_download(hf_readme_url))
    return readme_path
