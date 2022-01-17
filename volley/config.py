# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import importlib
from pathlib import Path
from typing import Any, Dict, Union

from yaml import Loader, load

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
        'volley.data_models.GenericMessage'
    is equivalent to:
        from volley.data_models import GenericMessage
    """
    modules = module_str.split(".")
    class_obj = modules[-1]
    pathmodule = ".".join(modules[:-1])
    module = importlib.import_module(pathmodule)
    t: type = getattr(module, class_obj)
    return t


def get_configs() -> Dict[str, Dict[str, Any]]:
    return load_yaml(GLOBALS)
