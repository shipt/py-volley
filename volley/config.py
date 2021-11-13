import os
from pathlib import Path
from typing import Dict, List

import yaml  # type: ignore
from yaml import Loader

from volley.logging import logger

CFG_FILE = Path(os.getenv("VOLLEY_CONFIG", "./volley_config.yml"))

ENV = os.getenv("APP_ENV", "localhost")


def load_config() -> Dict[str, List[Dict[str, str]]]:
    try:
        with CFG_FILE.open() as f:
            cfg: Dict[str, List[Dict[str, str]]] = yaml.load(f, Loader=Loader)
    except FileNotFoundError:
        _cfg = Path(__file__).parent.resolve().joinpath("default_config.yml")
        with _cfg.open() as f:
            cfg: Dict[str, List[Dict[str, str]]] = yaml.load(f, Loader=Loader)        
    return cfg
