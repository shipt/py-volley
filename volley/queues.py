from enum import Enum
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml  # type: ignore
from jinja2 import Template
from pydantic import BaseModel
from yaml import Loader

from volley.config import ENV
from volley.connectors.base import Consumer, Producer

# _cur_path = Path(__file__).parent.resolve().joinpath("config.yml")

CFG_FILE = Path(os.getenv("VOLLEY_CONFIG", "./volley_config.yml"))

class QueueType(str, Enum):
    kafka = "kafka"
    rsmq = "rsmq"
    postgres = "postgres"


class Queue(BaseModel):
    value: str
    model_schema: str
    type: QueueType

    # queue connection
    # TODO: figure out a good place for this to live
    # it should probably never take on a None value
    qcon: Optional[Union[Consumer, Producer]] = None


class Queues(BaseModel):
    queues: Dict[str, Queue]


def load_config() -> Dict[str, List[Dict[str, str]]]:
    with CFG_FILE.open() as f:
        cfg: Dict[str, List[Dict[str, str]]] = yaml.load(f, Loader=Loader)

    return cfg


def available_queues() -> Queues:
    cfg = load_config()

    kafka_env_map = {
        "production": "prd",
        "staging": "stg",
        "development": "dev",
        "localhost": "localhost",
    }
    kafka_env = kafka_env_map.get(ENV)
    queues = {}

    for q in cfg["queues"]:
        if q["type"] == "kafka":
            # interpolates environment prefix to templated kafka topic definitions
            _t = Template(q["value"])
            _value = _t.render(env=kafka_env)
        else:
            _value = q["value"]
        meta = Queue(value=_value, type=q["type"], model_schema=q["schema"])
        queues[q["name"]] = meta

    return Queues(queues=queues)
