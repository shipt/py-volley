# Copyright (c) Shipt.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import importlib
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, root_validator
from yaml import Loader, load  # type: ignore

GLOBALS = Path(__file__).parent.resolve().joinpath("global.yml")


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """loads a yaml to dict from Path object

    Raises FileNotFoundError
    """
    if isinstance(file_path, str):
        path = Path(file_path)
    else:
        path = file_path
    with path.open() as f:
        cfg: Dict[str, Any] = load(f, Loader=Loader)
    return cfg


def import_module_from_string(module_str: str) -> type:
    """returns the module given its string path
    for example:
        'volley.data_models.ComponentMessage'
    is equivalent to:
        from volley.data_models import ComponentMessage
    """
    modules = module_str.split(".")
    class_obj = modules[-1]
    pathmodule = ".".join(modules[:-1])
    module = importlib.import_module(pathmodule)
    t: type = getattr(module, class_obj)
    return t


def get_configs() -> Dict[str, Dict[str, Any]]:
    return load_yaml(GLOBALS)


class QueueConfig(BaseModel):
    name: str
    value: str
    profile: Optional[str]
    consumer: Optional[str]
    producer: Optional[str]
    model_handler: Optional[str]
    data_model: Optional[str]
    serializer: Optional[str]
    config: Optional[Dict[str, Any]]

    @root_validator
    @classmethod
    def validate_connectors(cls, values: dict[str, Any]) -> Any:
        """producer and consumer cannot both be omitted"""
        if values.get("producer") is None and values.get("consumer") is None:
            raise ValueError("Invalid Profile. Must provide one of `producer` or `consumer`")
        return values

    @root_validator
    @classmethod
    def validate_profile_definition(cls, values: dict[str, Any]) -> Any:
        """must specify the `profile` or specify all the profile attributes"""
        profile = values.get("profile")
        model_handler = values.get("model_handler")
        data_model = values.get("data_model")
        serializer = values.get("serializer")
        valid_profiles = get_configs()["profiles"]

        if profile in valid_profiles:
            return values
        elif profile is None and all(x in values for x in [model_handler, data_model, serializer]):
            # no profile provided but all connectors specified
            return values
        else:
            raise ValueError("Invalid configuration. must specify the `profile` or specify all the profile attributes.")
