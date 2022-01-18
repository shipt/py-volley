import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from confluent_kafka import Consumer, Message, Producer

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger

RUN_ONCE = False


@dataclass
class ConfluentKafkaConsumer(BaseConsumer):
    """
    Class to easily interact consuming message(s) from Kafka brokers.
    At a minimum bootstrap.servers and group.id must be set in the config dict
    """

    poll_interval: float = 10
    auto_offset_reset: str = "earliest"
    auto_commit_interval_ms: int = 3000

    def __post_init__(self) -> None:  # noqa: C901
        self.config = handle_creds(self.config)

        if "auto.offset.reset" not in self.config:
            logger.info("Assigning auto.offset.reset default: %s", self.auto_offset_reset)
            self.config["auto.offset.reset"] = self.auto_offset_reset

        if "auto.commit.interval.ms" not in self.config:
            logger.info("Assigning auto.commit.interval.ms default: %s", self.auto_commit_interval_ms)
            self.config["auto.commit.interval.ms"] = self.auto_commit_interval_ms

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

        # this is not overridable, due to the behavior in self.on_success()
        self.config["enable.auto.offset.store"] = False
        self.c = Consumer(self.config, logger=logger)
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
            return QueueMessage(message_context=message, message=message.value())

    def on_success(self, queue_name: str, message_context: Message) -> bool:
        self.c.store_offsets(message=message_context)  # committed according to auto.commit.interval.ms
        return True

    def on_fail(self, queue_name: str, message_context: Message) -> None:
        logger.info(
            "Downstream failure. Did not commit offset: %d, partition: %d, message: %s",
            message_context.offset(),
            message_context.partition(),
            message_context.value(),
        )
        pass

    def shutdown(self) -> None:
        self.c.close()
        logger.info("Successfully commit offsets and left consumer group %s", self.config.get("group.id"))


@dataclass
class ConfluentKafkaProducer(BaseProducer):
    """
    Class to easily interact producing message(s) to Kafka brokers.
    At a minimum bootstrap.servers must be set in the config dict
    """

    compression_type: str = "gzip"

    def __post_init__(self) -> None:  # noqa: C901
        self.config = handle_creds(self.config)
        if "compression.type" not in self.config:
            logger.info("Assigning compression.type default: %s", self.compression_type)
            self.config["compression.type"] = self.compression_type

        self.p = Producer(self.config, logger=logger)
        # self.config comes from super class
        logger.info("Kafka Producer Configuration: %s", self.config)

    def acked(self, err: Optional[str], msg: Message) -> None:
        if err is not None:
            logger.error("Failed to deliver message: %s, error: %s", msg.value(), err)
        else:
            logger.info(
                "Successful delivery to %s, partion: %d, offset: %d", msg.topic(), msg.partition(), msg.offset()
            )

    def produce(self, queue_name: str, message: bytes, **kwargs: Union[str, int]) -> bool:
        self.p.produce(
            key=kwargs.get("key"),
            topic=queue_name,
            value=message,
            headers=kwargs.get("headers"),
            callback=self.acked,
        )
        self.p.poll(0)
        logger.info("Sent to topic: %s", queue_name)
        return True

    def shutdown(self) -> None:
        self.p.flush()


def handle_creds(config_dict: Dict[str, Any]) -> Dict[str, Any]:
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
        sasl_password = os.getenv("KAFKA_SECRET")
        if (sasl_username is not None) and (sasl_password is not None):
            logger.info(
                "KAFKA_KEY and KAFKA_SECRET found in environment. Assigning security.protocol and sasl.mechanism"
            )
            config_dict["sasl.username"] = sasl_username
            config_dict["sasl.password"] = sasl_password
            config_dict["security.protocol"] = "SASL_SSL"
            config_dict["sasl.mechanism"] = "PLAIN"
    return config_dict
