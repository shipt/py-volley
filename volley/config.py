import importlib
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore
from yaml import Loader

from volley.logging import logger

GLOBALS = Path(__file__).parent.resolve().joinpath("global.yml")
CFG_FILE = Path(os.getenv("VOLLEY_CONFIG", "./volley_config.yml"))

APP_ENV = os.getenv("APP_ENV", "localhost")
METRICS_ENABLED = True
METRICS_PORT = 3000


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """loads a yaml to dict from Path object"""
    with file_path.open() as f:
        cfg: Dict[str, Any] = yaml.load(f, Loader=Loader)
    return cfg


def load_client_config() -> Dict[str, List[Dict[str, str]]]:
    """attemps to load the client provided config yaml
    falls back to the default_config file.
    #TODO: get rid of this. for testing we should just provide a config file
    """
    cfg: Dict[str, List[Dict[str, str]]] = {}
    try:
        cfg = load_yaml(CFG_FILE)
    except FileNotFoundError:
        logger.info(f"file {CFG_FILE} not found - falling back to default for testing")
        _cfg = Path(__file__).parent.resolve().joinpath("default_config.yml")
        cfg = load_yaml(_cfg)
    return cfg


def load_queue_configs() -> Dict[str, Dict[str, str]]:
    """loads client configurations for:
        - queues
        - connectors
        - data classes/schemas

    falls back to global configurations when client does not provide them
    """
    client_cfg: Dict[str, List[Dict[str, str]]] = load_client_config()
    return {k["name"]: k for k in client_cfg["queues"]}


def apply_defaults(config: Dict[str, List[Dict[str, str]]]) -> Dict[str, Dict[str, str]]:
    global_configs = load_yaml(GLOBALS)
    # handle default fallbacks
    global_connectors = global_configs["connectors"]
    default_queue_schema = global_configs["schemas"]["default"]

    queue_dict: Dict[str, Dict[str, str]] = {}
    for q in config["queues"]:
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
        queue_dict[q["name"]] = q
    return queue_dict


def import_module_from_string(module_str: str) -> Any:
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
    return getattr(module, class_obj)
