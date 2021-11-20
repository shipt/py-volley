from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Union

from jinja2 import Template

from volley.config import APP_ENV, GLOBALS, import_module_from_string, load_yaml
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


def yaml_to_dict_config(queues: List[str], yaml_path: str) -> Dict[str, List[dict[str, str]]]:
    """loads config from yaml then filters to those needed for specific implementation

    yaml config file is allowed to contain more configurations than needed
    """
    cfg: Dict[str, List[dict[str, str]]] = load_yaml(file_path=yaml_path)

    out_configs: Dict[str, List[dict[str, str]]] = {"queues": []}
    for q_config in cfg["queues"]:
        if q_config["name"] in queues:
            q_config = interpolate_kafka_topics(q_config)
            out_configs["queues"].append(q_config)

    return cfg


def dict_to_config(config: dict[str, dict[str, str]]) -> dict[str, List[dict[str, str]]]:
    # assign the name of the queue to the queue object
    for qname, _config in config.items():
        _config["name"] = qname
    # put all queues configs into a list
    standard_schema = {"queues": [v for k, v in config.items()]}
    # configuration is now in same schema as yaml
    return standard_schema


def apply_defaults(config: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
    global_configs = load_yaml(GLOBALS)
    global_connectors = global_configs["connectors"]
    default_queue_schema = global_configs["schemas"]["default"]

    # apply default queue configurations
    for queue in config["queues"]:
        # for each defined queue, validate there is a consumer & producer defined
        # or fallback to the global default
        q_type = queue["type"]
        for conn in ["consumer", "producer"]:
            if conn not in queue:
                # if there isn't a connector (produce/consume) defined,
                #   assign it from global defalt
                queue[conn] = global_connectors[q_type][conn]
        # handle data schema
        if "schema" not in queue:
            queue["schema"] = default_queue_schema

    return config


def config_to_queue_map(configs: List[dict[str, Any]]) -> Dict[str, Queue]:
    """

    Overrides anything in yaml.

    Returns a map of {queue_name: Queue}
    """
    input_output_queues: Dict[str, Queue] = {}

    for q in configs:
        qname = q["name"]
        try:
            input_output_queues[qname] = Queue(
                name=qname,
                value=q["value"],
                schema=q["schema"],
                type=q["type"],
                consumer=q["consumer"],
                producer=q["producer"],
            )
        except KeyError:
            logger.warning(f"Queue '{qname}' not found in configuraiton")
    return input_output_queues


def available_queues(yaml_path: str) -> Dict[str, Queue]:
    """returns a mapping of all the queues defined in configuration
    useful for utilizies that might want to work with all queues, such as a healthcheck
    """
    cfg = load_yaml(yaml_path)

    for queue_config in cfg["queues"]:
        queue_config = interpolate_kafka_topics(queue_config)
    cfg = apply_defaults(cfg)

    return config_to_queue_map(cfg["queues"])


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
