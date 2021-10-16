import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml  # type: ignore
from jinja2 import Template
from pydantic import BaseModel
from yaml import Loader

from engine.consumer import Consumer
from engine.producer import Producer

_cur_path = Path(__file__).parent.resolve().joinpath("config.yml")


class QueueType(str, Enum):
    kafka = "kafka"
    rsmq = "rsmq"
    postgres = "postgres"


class Queue(BaseModel):
    value: str
    type: QueueType

    # queue connection
    # TODO: figure out a good place for this to live
    # it should probably never take on a None value
    q: Optional[Union[Consumer, Producer]] = None


class Queues(BaseModel):
    queues: Dict[str, Queue]


def load_config() -> Dict[str, List[Dict[str, str]]]:
    with _cur_path.open() as f:
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
    kafka_env = kafka_env_map.get(os.getenv("APP_ENV", "localhost"))
    queues = {}

    for q in cfg["queues"]:
        if q["type"] == "kafka":
            # interpolates environment prefix to templated kafka topic definitions
            _t = Template(q["value"])
            _value = _t.render(env=kafka_env)
        else:
            _value = q["value"]
        meta = Queue(value=_value, type=q["type"])
        queues[q["name"]] = meta

    return Queues(queues=queues)
