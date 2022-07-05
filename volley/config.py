# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from yaml import Loader, load

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.models.base import BaseModelHandler
from volley.serializers.base import BaseSerialization

GLOBALS = Path(__file__).parent.resolve().joinpath("global.yml")


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """loads a yaml to dict from Path object
    Raises FileNotFoundError
    """
    if isinstance(file_path, str):
        path = Path(file_path)
    else:
        path = file_path
    with path.open() as f:
        cfg: Dict[str, Any] = load(f, Loader=Loader)
    return cfg


def import_module_from_string(module_str: str) -> type:
    """returns the module given its string path
    for example:
        'volley.data_models.GenericMessage'
    is equivalent to:
        from volley.data_models import GenericMessage
    """
    modules = module_str.split(".")
    class_obj = modules[-1]
    pathmodule = ".".join(modules[:-1])
    module = importlib.import_module(pathmodule)
    t: type = getattr(module, class_obj)
    return t


def get_configs() -> Dict[str, Dict[str, Any]]:
    return load_yaml(GLOBALS)


@dataclass
class QueueConfig:
    """Represents the configuration for a single queue. Provides the
    application with necessary configuration for interacting with the
    specified queue.

    Example:

    ```python
    input_cfg = QueueConfig(
        name="my-input-queue",
        value="my.input.kafka.topic",
        profile="confluent",
        config={"consumer.group": "my_consumer_group", "bootstrap.servers": "kafka:9092"}
    )
    output_cfg = QueueConfig(
        name="my-output-queue",
        value="my.output.kafka.topic",
        profile="confluent",
        config={"bootstrap.servers": "kafka:9092"}
    )
    app = Engine(
        app_name="my-app",
        input_queue="my-input-queue",
        output_queues=["my-output-queue"],
        queue_config=[input_cfg, output_cfg]
    )
    ```
    """

    name: str
    value: str
    profile: Optional[str] = None
    consumer: Optional[Union[str, Type[BaseConsumer]]] = None
    producer: Optional[Union[str, Type[BaseProducer]]] = None
    model_handler: Optional[Union[str, Type[BaseModelHandler]]] = None
    serializer: Optional[Union[str, Type[BaseSerialization]]] = None
    config: Optional[Dict[Any, Any]] = None

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """transform to dictionary omitting optional fields when not provided"""
        not_none = {k: v for k, v in self.__dict__.items() if v is not None}
        return {self.name: not_none}
