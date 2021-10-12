from pathlib import Path
from typing import Dict, List, Union, Optional

import yaml
from yaml import Loader

from pydantic import BaseModel
from engine.consumer import Consumer
from engine.producer import Producer
from enum import Enum

from jinja2 import Template
import os


_cur_path = Path(__file__).parent.resolve().joinpath("config.yml")



class QueueType(str, Enum):
    kafka = "kafka"
    rsmq = "rsmq"


class Queue(BaseModel):
    value: str
    type: QueueType
    
    # queue connection
    q: Optional[Union[Consumer, Producer]] = None


class Queues(BaseModel):
    queues: Dict[str, Queue]


def available_queues() -> Queues:
    with _cur_path.open() as f:
        cfg: Dict[str, List[Dict[str, str]]] = yaml.load(f, Loader=Loader)
    kafka_env_map = {
        "production": "prd",
        "staging": "stg",
        "development": "dev",
        "localhost": "localhost"
    }
    kafka_env = kafka_env_map.get(os.getenv("APP_ENV", "localhost"))
    queues = {}

    for q in cfg["queues"]:
        if q["type"] == "kafka":
            _t = Template(q["value"])
            _value = _t.render(env=kafka_env)
        else:
            _value = q["value"]
        meta = Queue(value=_value, type=q["type"])
        queues[q["name"]] = meta
    q = {"queues": queues}
    return Queues(**q)
