# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import importlib
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel
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


class QueueConfig(BaseModel):
    """Represents the configuration for a single queue. Provides the
    application with necessary configuration for interacting with the
    specified queue.

    Attributes:
        name (str): Alias for a particular queue.
        value (str): The system name for a queue.
            For example, the name of a Kafka topic (prd.my.long.kafka.topic.name) or name of a RSMQ queue.
        profile (Optional[str]): Either `kafka|rsmq`.
            Pertains to the type of connector required to produce and consume from the queue.
            If not provided, must provide values for ALL of `consumer, producer, serializer, model_handler`.
        data_model (Optional[str]): Defaults to `volley.data_models.GenericMessage`.
            Path to the Pydantic model used for data validation.
            When default is used, Volley will only validate that messages can be successfully
            converted to a Pydantic model or dictionary.
        serializer (Optional[str]): Defaults to `volley.serializers.OrJsonSerializer`.
            Path to the serializer.
        producer (Optional[str]): Used for providing a custom producer connector.
            Overrides the producer pertaining to that provided in `type`.
            Provide the dot path to the producer class. e.g. for Kafka,defaults to
            `volley.connectors.kafka.KafkaProducer`;
            cf. [Extending Connectors](./connectors/connectors.md#extending-connectors-with-plugins).
        consumer (Optional[str]): Used for providing a custom consumer connector.
            Overrides the consumer pertaining to that provided in `type`.
            Provide the dot path to the consumer class.
            e.g. for Kafka, defaults to `volley.connectors.kafka.KafkaConsumer`;
            cf. [Extending Connectors](./connectors/connectors.md#extending-connectors-with-plugins).
        config: (Optional[str]): Any configuration to be passed directly to the queue connector. For example,
            all [librdkafka configurations](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md)
            can be passed through to the connector via a dictionary here.

    # Example

    ```python
    from volley import Engine, QueueConfig

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
    data_model: Optional[Union[str, Any]] = None
    model_handler: Optional[Union[str, Type[BaseModelHandler]]] = None
    serializer: Optional[Union[str, Type[BaseSerialization]]] = None
    config: Optional[Dict[Any, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """transform to dictionary omitting optional fields when not provided"""
        return {k: v for k, v in self.__dict__.items() if v is not None}
