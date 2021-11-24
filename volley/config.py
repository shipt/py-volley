import importlib
import os
from pathlib import Path
from typing import Any, Dict, Union

import yaml  # type: ignore
from yaml import Loader

from volley.logging import logger

GLOBALS = Path(__file__).parent.resolve().joinpath("global.yml")

APP_ENV = os.getenv("APP_ENV", "localhost")
METRICS_ENABLED = True
METRICS_PORT = 3000


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """loads a yaml to dict from Path object

    Raises FileNotFoundError
    """
    if isinstance(file_path, str):
        path = Path(file_path)
    else:
        path = file_path
    try:
        with path.open() as f:
            cfg: Dict[str, Any] = yaml.load(f, Loader=Loader)
    except FileNotFoundError:
        logger.error(f"file {file_path} not found")
        raise
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
