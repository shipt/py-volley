import importlib
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore
from yaml import Loader

from volley.logging import logger

GLOBALS = Path(__file__).parent.resolve().joinpath("global.yml")
CFG_FILE = Path(os.getenv("VOLLEY_CONFIG", "./volley_config.yml"))

ENV = os.getenv("APP_ENV", "localhost")
METRICS_ENABLED = True
METRICS_PORT = 3000


def load_config(file_path: Path) -> Dict[str, Any]:
    with file_path.open() as f:
        cfg: Dict[str, Any] = yaml.load(f, Loader=Loader)
    return cfg


def load_client_config() -> Dict[str, List[Dict[str, str]]]:
    cfg: Dict[str, List[Dict[str, str]]] = {}
    try:
        cfg = load_config(CFG_FILE)
    except FileNotFoundError:
        logger.info(f"file {CFG_FILE} not found - falling back to default for testing")
        _cfg = Path(__file__).parent.resolve().joinpath("default_config.yml")
        cfg = load_config(_cfg)
    return cfg


def get_application_config() -> Dict[str, List[Dict[str, str]]]:
    """loads client configurations for:
        - queues
        - connectors
        - data classes/schemas

    falls back to global configurations when client does not provide them
    """
    client_cfg = load_client_config()
    global_configs = load_config(GLOBALS)

    # handle default fallbacks
    global_connectors = global_configs["connectors"]
    default_queue_schema = global_configs["schemas"]["default"]

    for q in client_cfg["queues"]:
        # for each defined queue, validate there is a consumer & producer defined
        # or fallback to the global default
        q_type = q["type"]
        for conn in ["consumer", "producer"]:
            if conn not in q:
                # if there isn't a connector (produce/consume) defined,
                #   assign it from global defalt
                q[conn] = global_connectors[q_type][conn]
        # handle data schema
        if "schema" not in q:
            q["schema"] = default_queue_schema

    return client_cfg


def import_module_from_string(module: str) -> Any:
    """returns the module given its string path
    for example:
        'volley.data_models.ComponentMessage'
    is equivalent to:
        from volley.data_models import ComponentMessage
    """
    modules = module.split(".")
    class_obj = modules[-1]
    pathmodule = ".".join(modules[:-1])
    module = importlib.import_module(pathmodule)
    return getattr(module, class_obj)
