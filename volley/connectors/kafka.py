import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Union

from confluent_kafka import Consumer as KConsumer
from confluent_kafka import Producer as KProducer

from volley.config import APP_ENV
from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage
from volley.logging import logger

RUN_ONCE = False


@dataclass
class KafkaConsumer(Consumer):
    """
    Class to easily interact consuming message(s) from Kafka brokers.
    At a minimum brokers and consumer_group must be set
    """

    poll_interval: Optional[float] = 10
    brokers: str = os.environ["KAFKA_BROKERS"]
    username: Optional[str] = os.getenv("KAFKA_KEY")
    password: Optional[str] = os.getenv("KAFKA_SECRET")
    auto_offset_reset: Optional[
        Literal["smallest", "earliest", "beginning", "largest", "latest", "end", "error"]
    ] = "earliest"
    config_override: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        offset_options = ["smallest", "earliest", "beginning", "largest", "latest", "end", "error"]
        if self.auto_offset_reset not in offset_options:
            raise ValueError(f"auto_offset_reset must be : {offset_options}")

        self.config.update(
            {
                "bootstrap.servers": self.brokers,
                "auto.offset.reset": self.auto_offset_reset,
            }
        )
        # No key == dev mode
        if self.username is not None and self.password is not None:
            self.config.update(
                {
                    "sasl.username": self.username,
                    "sasl.password": self.password,
                    "security.protocol": "SASL_SSL",
                    "sasl.mechanism": "PLAIN",
                }
            )
        if self.config_override is not None:
            self.config.update(self.config_override)

        # self.config provided from base Consumer class
        # consumer group assignment
        # try config, then env var, then command line argument w/ env
        if "group.id" in self.config:
            # we'll pass the config directly into Kafka constructor
            pass
        else:
            try:
                self.config["group.id"] = os.environ["KAFKA_CONSUMER_GROUP"]
            except KeyError:
                # TODO: need a better way to do this
                # keeping to prevent breaking change
                logger.warning("KAFKA_CONSUMER_GROUP not specified in environment")
                try:
                    component_name = sys.argv[1]
                    self.config["group.id"] = f"{APP_ENV}_{component_name}"
                except Exception:
                    logger.exception("Kafka Consumer group not specified")
                    raise

        if "poll_interval" in self.config:
            # poll_interval can be overridden by a user provided Engine init config
            # but it should not be passed to base Confluent Consumer init
            # confluent will ignore it with a warning, however
            self.poll_interval = self.config.pop("poll_interval")

        self.c = KConsumer(
            self.config,
            # TODO: develop commit strategy to minimize duplicates and guarantee no loss
            # config_override={"enable.auto.offset.store": False}
        )
        logger.info("Kafka Consumer Configuration: %s", self.config)
        self.c.subscribe([self.queue_name])
        logger.info("Subscribed to %s", self.queue_name)

    def consume(  # type: ignore
        self,
        queue_name: str = None,
    ) -> Optional[QueueMessage]:
        if queue_name is None:
            queue_name = self.queue_name

        message = self.c.poll(self.poll_interval)
        if message is None:
            pass
        elif message.error():
            logger.warning(message.error())
            message = None
        else:
            return QueueMessage(message_id=message, message=message.value())

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        # self.c.consumer.store_offsets(message=message_id)
        return True

    def on_fail(self) -> None:
        pass

    def shutdown(self) -> None:
        self.c.close()


@dataclass
class KafkaProducer(Producer):
    """
    Class to easily interact producing message(s) to Kafka brokers.
    At a minimum brokers must be set.
    """

    brokers: str = os.environ["KAFKA_BROKERS"]
    username: Optional[str] = os.getenv("KAFKA_KEY")
    password: Optional[str] = os.getenv("KAFKA_SECRET")
    compression_type: Optional[Literal[None, "gzip", "snappy", "lz4", "zstd", "inherit"]] = "gzip"
    config_override: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        compression_type_options = [None, "gzip", "snappy", "lz4", "zstd", "inherit"]
        if self.compression_type not in compression_type_options:
            raise ValueError(f"compression_type must be option: {compression_type_options}")

        self.config.update({"bootstrap.servers": self.brokers, "compression.type": self.compression_type})
        # No key == dev mode
        if self.username is not None and self.password is not None:
            self.config.update(
                {
                    "sasl.username": self.username,
                    "sasl.password": self.password,
                    "security.protocol": "SASL_SSL",
                    "sasl.mechanism": "PLAIN",
                }
            )
        if self.config_override is not None:
            self.config.update(self.config_override)

        self.p = KProducer(self.config)
        # self.config comes from super class
        logger.info("Kafka Producer Configuration: %s", self.config)

    def produce(self, queue_name: str, message: bytes, **kwargs: Union[str, int]) -> bool:
        if kwargs.get("serialize"):
            message = json.dumps(message).encode()
        elif not isinstance(message, (str, bytes)):
            value_type = type(message)
            raise TypeError(f"`value` must be type str|bytes, or set the `serialize` parameter to True - {value_type=}")
        self.p.produce(
            key=kwargs.get("key"),
            topic=queue_name,
            value=message,
            headers=kwargs.get("headers"),
        )
        return True

    def shutdown(self) -> None:
        self.p.flush()
