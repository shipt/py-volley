import abc
from enum import Enum
from typing import Dict, Optional, Union

from jinja2 import Template
from pydantic import BaseModel

from volley.config import ENV, get_application_config, import_module_from_string
from volley.connectors.base import Consumer, Producer


class QueueType(str, Enum):
    kafka = "kafka"
    rsmq = "rsmq"
    postgres = "postgres"


class Queue(BaseModel):
    value: str
    model_schema: str
    type: QueueType

    consumer_class: abc.ABCMeta
    producer_class: abc.ABCMeta

    # queue connection
    qcon: Optional[Union[Consumer, Producer]] = None


class Queues(BaseModel):
    queues: Dict[str, Queue]


def available_queues() -> Queues:
    cfg = get_application_config()

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

        meta = Queue(
            value=_value,
            type=q["type"],
            model_schema=q["schema"],
            consumer_class=import_module_from_string(q["consumer"]),
            producer_class=import_module_from_string(q["producer"]),
        )
        queues[q["name"]] = meta

    return Queues(queues=queues)
