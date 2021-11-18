from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from jinja2 import Template
from pydantic import BaseModel

from volley.config import APP_ENV, import_module_from_string, load_queue_configs
from volley.connectors.base import Consumer, Producer
from volley.data_models import ComponentMessage
from volley.logging import logger


class ConnectionType(Enum):
    """types of connections to queues"""

    PRODUCER: auto = auto()
    CONSUMER: auto = auto()


@dataclass
class Queue:
    # alias for the queue
    name: str
    # system name for the queue. for example, some really long kafka topic name
    value: str

    model_schema: str
    type: str

    consumer_class: str
    producer_class: str

    # initialized queue connection
    consumer_con: Consumer = field(init=False)
    producer_con: Producer = field(init=False)

    # initialized schema model
    model_class: Union[ComponentMessage, Dict[str, Any]] = field(init=False)

    def connect(self, con_type: ConnectionType) -> None:
        if con_type == ConnectionType.CONSUMER:
            _class = import_module_from_string(self.consumer_class)
            self.consumer_con = _class(queue_name=self.value)
        elif con_type == ConnectionType.PRODUCER:
            _class = import_module_from_string(self.producer_class)
            self.producer_con = _class(queue_name=self.value)
        else:
            logger.error(f"{con_type=} is not valid")

    def init_schema(self) -> None:
        if self.model_schema in ["dict"]:
            self.model_class = dict  # type: ignore
        else:
            self.model_class = import_module_from_string(self.model_schema)


def queues_from_yaml(queues: List[str]) -> Dict[str, Queue]:
    """loads config from yaml then filters to queues needed for specific implementation

    Returns a map of {queue_name: Queue}
    """
    cfg = load_queue_configs()

    input_output_queues: Dict[str, Queue] = {}

    for q in queues:
        q_config = interpolate_kafka_topics(cfg[q])
        try:
            input_output_queues[q] = Queue(
                name=q,
                value=q_config["value"],
                model_schema=q_config["schema"],
                type=q_config["type"],
                consumer_class=q_config["consumer"],
                producer_class=q_config["producer"],
            )
        except KeyError:
            logger.warning(f"Queue '{q}' not found in configuraiton")
    return input_output_queues


def interpolate_kafka_topics(cfg: Dict[str, str]) -> Dict[str, str]:
    """interpolates Shipt env prefix to templates kafka topic"""
    kafka_env_map = {
        "production": "prd",
        "staging": "stg",
        "development": "dev",
        "localhost": "localhost",
    }
    kafka_env = kafka_env_map.get(APP_ENV)

    if cfg["type"] == "kafka":
        _t = Template(cfg["value"])
        cfg["value"] = _t.render(env=kafka_env)
    return cfg


def available_queues() -> Dict[str, Queue]:
    cfg = load_queue_configs()

    queues = {}

    for q_name, queue_dict in cfg.items():
        queue_dict = interpolate_kafka_topics(queue_dict)
        meta = Queue(
            name=q_name,
            value=queue_dict["value"],
            type=queue_dict["type"],
            model_schema=queue_dict["schema"],
            consumer_class=queue_dict["consumer"],
            producer_class=queue_dict["producer"],
        )
        queues[q_name] = meta

    return queues
