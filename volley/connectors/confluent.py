import os
import sys
from dataclasses import dataclass
from typing import Literal, Optional, Union, Dict

from confluent_kafka import Consumer as KConsumer
from confluent_kafka import Producer as KProducer

from volley.config import APP_ENV
from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage
from volley.logging import logger

RUN_ONCE = False


@dataclass
class ConfluentKafkaConsumer(Consumer):
    """
    Class to easily interact consuming message(s) from Kafka brokers.
    At a minimum bootstrap.servers and group.id must be set in the config dict
    """

    poll_interval: Optional[float] = 10
    auto_offset_reset: Optional[
        Literal["smallest", "earliest", "beginning", "largest", "latest", "end", "error"]
    ] = "earliest"

    def __post_init__(self) -> None:  # noqa: C901
        self.config = handle_creds(self.config)
        self.config["auto.offset.reset"] = self.auto_offset_reset

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
                logger.exception("KAFKA_CONSUMER_GROUP not specified in env variable or group.id in config dict")
                raise

        if "poll_interval" in self.config:
            # poll_interval can be overridden by a user provided Engine init config
            # but it should not be passed to base Confluent Consumer init
            # confluent will ignore it with a warning, however
            self.poll_interval = self.config.pop("poll_interval")

        self.c = KConsumer(self.config)
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
class ConfluentKafkaProducer(Producer):
    """
    Class to easily interact producing message(s) to Kafka brokers.
    At a minimum bootstrap.servers must be set in the config dict
    """

    username: Optional[str] = os.getenv("KAFKA_KEY")
    password: Optional[str] = os.getenv("KAFKA_SECRET")
    compression_type: Optional[Literal[None, "gzip", "snappy", "lz4", "zstd", "inherit"]] = "gzip"

    def __post_init__(self) -> None:  # noqa: C901
        self.config = handle_creds(self.config)
        self.config.update({"compression.type": self.compression_type})

        self.p = KProducer(self.config)
        # self.config comes from super class
        logger.info("Kafka Producer Configuration: %s", self.config)

    def produce(self, queue_name: str, message: bytes, **kwargs: Union[str, int]) -> bool:
        self.p.produce(
            key=kwargs.get("key"),
            topic=queue_name,
            value=message,
            headers=kwargs.get("headers"),
        )
        return True

    def shutdown(self) -> None:
        self.p.flush()


def handle_creds(config: dict) -> Dict[str, str]:
    config_dict = config.copy()
    if "bootstrap.servers" in config_dict:
        pass
    else:
        try:
            config_dict["bootstrap.servers"] = os.environ["KAFKA_BROKERS"]
        except KeyError:
            logger.exception("Kafka brokers not specified, set in config dict or env var KAFKA_BROKERS")
            raise

    # No key == dev mode
    if config_dict.get("sasl.username") and config_dict.get("sasl.password"):
        pass
    else:
        sasl_username = os.getenv("KAFKA_KEY")
        sasl_password = os.getenv("KAFKA_SCRET")
        if (sasl_username is not None) and (sasl_password is not None):
            config_dict["sasl.username"] = sasl_username
            config_dict["sasl.password"] = sasl_password
            config_dict["security.protocol"] = "SASL_SSL"
            config_dict["sasl.mechanism"] = "PLAIN"
    return config_dict

