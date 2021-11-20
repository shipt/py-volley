from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Union

from jinja2 import Template

from volley.config import (
    APP_ENV,
    apply_defaults,
    import_module_from_string,
    load_queue_configs,
)
from volley.connectors.base import Consumer, Producer
from volley.data_models import ComponentMessage
from volley.logging import logger


class ConnectionType(Enum):
    """types of connections to queues"""

    PRODUCER: auto = auto()
    CONSUMER: auto = auto()


@dataclass
class Queue:
    """a Queue object represents everything we need to know about a queue
    and is modeled off the configuration files for a queue
    """

    # alias for the queue
    name: str
    # system name for the queue. for example, some really long kafka topic name
    value: str

    schema: str
    type: str

    consumer: str
    producer: str

    # initialized queue connection
    # these get initialized by calling connect()
    consumer_con: Consumer = field(init=False)
    producer_con: Producer = field(init=False)

    # initialized schema model
    # these gets loaded by calling init_schema()
    model_class: Union[ComponentMessage, Dict[str, Any]] = field(init=False)

    def connect(self, con_type: ConnectionType) -> None:
        if con_type == ConnectionType.CONSUMER:
            _class = import_module_from_string(self.consumer)
            self.consumer_con = _class(queue_name=self.value)
        elif con_type == ConnectionType.PRODUCER:
            _class = import_module_from_string(self.producer)
            self.producer_con = _class(queue_name=self.value)
        else:
            logger.error(f"{con_type=} is not valid")

    def init_schema(self) -> None:
        if self.schema in ["dict"]:
            self.model_class = dict  # type: ignore
        else:
            self.model_class = import_module_from_string(self.schema)


def queues_from_yaml(queues: List[str]) -> Dict[str, Queue]:
    """loads config from yaml then filters to queues needed for specific implementation

    Returns a map of {queue_name: Queue}
    """
    cfg: Dict[str, Dict[str, str]] = load_queue_configs()

    return queues_from_dict(cfg)


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
    """returns a mapping of all the queues defined in configuration
    useful for utilizies that might want to work with all queues, such as a healthcheck
    """
    cfg = load_queue_configs()

    queues = {}

    for q_name, queue_dict in cfg.items():
        queue_dict = interpolate_kafka_topics(queue_dict)
        meta = Queue(
            name=q_name,
            value=queue_dict["value"],
            type=queue_dict["type"],
            schema=queue_dict["schema"],
            consumer=queue_dict["consumer"],
            producer=queue_dict["producer"],
        )
        queues[q_name] = meta

    return queues


def queues_from_dict(config: dict[str, Any]) -> Dict[str, Queue]:
    """loads config from user provided dictionary.

    Overrides anything in yaml.

    Returns a map of {queue_name: Queue}
    """

    # put all queues configs into a list
    queue_list = [v for k, v in config.items()]
    for_default_check = {"queues": queue_list}
    config = apply_defaults(for_default_check)
    input_output_queues: Dict[str, Queue] = {}

    for qname, config in config.items():
        try:
            input_output_queues[qname] = Queue(
                name=qname,
                value=config["value"],
                schema=config["schema"],
                type=config["type"],
                consumer=config["consumer"],
                producer=config["producer"],
            )
        except KeyError:
            logger.warning(f"Queue '{qname}' not found in configuraiton")
    return input_output_queues
