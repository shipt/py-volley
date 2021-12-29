import importlib
import os
from pathlib import Path
from typing import Any, Dict, Union

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
