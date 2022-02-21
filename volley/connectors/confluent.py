import os
from dataclasses import dataclass
from threading import Thread
from typing import Any, Dict, Optional, Union

from confluent_kafka import Consumer, Message, Producer
from prometheus_client import Counter

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger

DELIVERY_STATUS = Counter("delivery_report_status", "Kafka delivered message", ["status"])


@dataclass
class ConfluentKafkaConsumer(BaseConsumer):
    """
    Use for consuming a single message from a single Kafka topic.

    Built on confluent-kafka-python/librdkafka. Offsets are stored in librdkafka
        and commited according to auto.commit.interval.ms
        https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    """

    poll_interval: float = 10
    auto_offset_reset: str = "earliest"
    auto_commit_interval_ms: int = 3000

    def __post_init__(self) -> None:  # noqa: C901
        # mapping of partition/offset of the last stored commit
        self.last_offset: Dict[int, int] = {}

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
        # on_success calls store_offsets()
        self.config["enable.auto.offset.store"] = False
        self.c = Consumer(self.config, logger=logger)
        logger.info("Kafka Consumer Configuration: %s", self.config)
        self.c.subscribe([self.queue_name])
        logger.info("Subscribed to %s", self.queue_name)

    def consume(  # type: ignore
        self,
    ) -> Optional[QueueMessage]:
        message = self.c.poll(self.poll_interval)
        if message is None:
            pass
        elif message.error():
            logger.warning(message.error())
            message = None
        else:
            return QueueMessage(message_context=message, message=message.value())

    def on_success(self, message_context: Message) -> None:
        """stores any offsets that are able to be stored"""
        partition = message_context.partition()
        this_offset = message_context.offset()

        # see if we've already committed this or a higher offset
        # delivery report from kafka producer are not guaranteed to be in order
        # that they were produced
        # https://github.com/confluentinc/confluent-kafka-python/issues/300#issuecomment-358416432
        try:
            last_commit = self.last_offset[partition]
        except KeyError:
            # first message from this partition
            self.last_offset[partition] = this_offset
            self.c.store_offsets(message_context)
            return
        if this_offset > last_commit:
            self.c.store_offsets(message_context)  # committed according to auto.commit.interval.ms
            self.last_offset[partition] = this_offset

    def on_fail(self, message_context: Message) -> None:
        logger.error(
            "Downstream failure. Did not commit offset: %d, partition: %d, message: %s",
            message_context.offset(),
            message_context.partition(),
            message_context.value(),
        )

    def shutdown(self) -> None:
        self.c.close()
        logger.info("Successfully commit offsets and left consumer group %s", self.config.get("group.id"))


@dataclass
class ConfluentKafkaProducer(BaseProducer):
    compression_type: str = "gzip"
    thread: bool = False
    poll_thread_timeout: float = 1.0

    def __post_init__(self) -> None:  # noqa: C901
        self.callback_delivery = True
        self.config = handle_creds(self.config)
        if "compression.type" not in self.config:
            logger.info("Assigning compression.type default: %s", self.compression_type)
            self.config["compression.type"] = self.compression_type

        self.p = Producer(self.config, logger=logger)
        # self.config comes from super class
        logger.info("Kafka Producer Configuration: %s", self.config)

        # producer poll thread
        self.kill_poll_thread = False
        if "poll_thread_timeout" in self.config:
            self.poll_thread_timeout = self.config.pop("poll_thread_timeout")

    def init_callbacks(self, consumer: BaseConsumer, thread: bool = True) -> None:
        # daemon thread - this can be aggressively killed on shutdown
        # Volley will call shutdown() which will trigger confluent.Producer.flush()
        # flush() will trigger acked() and call consumers on_success/on_fail
        self.on_success = consumer.on_success
        self.on_fail = consumer.on_fail
        if thread:
            self.thread = True
            self.poll_thread = Thread(target=self.handle_poll, daemon=True)
            self.poll_thread.start()

    def handle_poll(self) -> None:
        while not self.kill_poll_thread:
            self.p.poll(0.2)

    def acked(self, err: Optional[str], msg: Message, consumer_context: Any) -> None:
        if err is not None:
            logger.critical(
                "Failed delivery to %s, message: %s, error: %s",
                msg.topic(),
                msg.value(),
                err,
            )
            DELIVERY_STATUS.labels("fail").inc()
            self.on_fail(consumer_context)  # type: ignore

        else:
            logger.debug(
                "Successful delivery to %s, partion: %d, offset: %d", msg.topic(), msg.partition(), msg.offset()
            )
            DELIVERY_STATUS.labels("success").inc()
            self.on_success(consumer_context)  # type: ignore

    def produce(self, queue_name: str, message: bytes, message_context: Any, **kwargs: Union[str, int]) -> bool:
        self.p.produce(
            key=kwargs.get("key"),
            topic=queue_name,
            value=message,
            headers=kwargs.get("headers"),
            callback=lambda err, msg, obj=message_context: self.acked(err, msg, obj),
        ),

        logger.debug("Sent to topic: %s", queue_name)
        return True

    def shutdown(self) -> None:
        self.p.flush()
        if self.thread:
            self.kill_poll_thread = True
            self.poll_thread.join(self.poll_thread_timeout)


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
