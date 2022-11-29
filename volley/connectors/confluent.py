import logging
import os
import signal
from dataclasses import dataclass, field
from threading import Thread
from typing import Any, Dict, List, Optional, Union

from confluent_kafka import Consumer, Message, Producer
from prometheus_client import Counter

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage

logger = logging.getLogger(__name__)

DELIVERY_STATUS = Counter("delivery_report_status", "Kafka delivered message", ["status"])


@dataclass
class ConfluentKafkaConsumer(BaseConsumer):
    """
    Use for consuming a single message from a single Kafka topic.

    Built on confluent-kafka-python/librdkafka. Offsets are stored in librdkafka
        and committed according to auto.commit.interval.ms
        https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md

    ## Multi-topic subscription
    You may find yourself wanting to configure a single Volley worker to consume from multiple Kafka topics,
    each with the same message schema. You can do this by specifying the queue value as a comma
    separated list of topics:

    ```python hl_lines="4"
    cfg = {
        "input-topic": {
            "profile": "confluent",
            "value": "kafka.topic.0,kafka.topic.1",
            "consumer": "volley.connectors.confluent.ConfluentKafkaConsumer",
            "config": {"bootstrap.servers": "kafka:9092", "group.id": "myConsumerGroup"},
        },
    }
    ```

    Note: multi-topic is only supported for consumption.
    Volley will only be able to *consume* to the queue as configured above.
    To produce to multiple topics, specify each topic as a separate queue and publish to them.

    ```python
    return [
        ("output-topic-0", message_object),
        ("output-topic-1", message_object)
    ]
    ```

    """

    poll_interval: float = 10
    auto_offset_reset: str = "earliest"
    auto_commit_interval_ms: int = 3000
    stop_on_failure: bool = True
    # mapping of topic -> partition/offset of the last stored commit
    last_offset: Dict[str, Dict[int, int]] = field(init=False)

    def __post_init__(self) -> None:  # noqa: C901
        self.config = handle_creds(self.config)

        if "auto.offset.reset" not in self.config:
            logger.info("Assigning auto.offset.reset default: %s", self.auto_offset_reset)
            self.config["auto.offset.reset"] = self.auto_offset_reset

        if "auto.commit.interval.ms" not in self.config:
            logger.info("Assigning auto.commit.interval.ms default: %s", self.auto_commit_interval_ms)
            self.config["auto.commit.interval.ms"] = self.auto_commit_interval_ms

        if "stop_on_failure" in self.config:
            self.stop_on_failure = self.config["stop_on_failure"]

        if self.stop_on_failure:
            logger.info(
                "`stop_on_failure` = %s. Application will gracefully shutdown when" "there are downstream failures.",
                self.stop_on_failure,
            )
        else:
            logger.warning(
                "`stop_on_failure` = %s. Application will log a CRITICAL level message"
                "and continue processing on downstream failures.",
                self.stop_on_failure,
            )
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

        # https://github.com/apache/kafka/blob/
        # 8007211cc982d8458223e866c1ee7d94b69e0249/core/src/main/scala/kafka/common/Topic.scala#L29
        # "," are not allowed in Apache Kafka topic names.
        # Allow multi-topic subscription by supplying a comma separated lists of topics
        topics: List[str] = self.queue_name.split(",")
        self.c.subscribe(topics)

        self.last_offset = {topic: {} for topic in topics}

        logger.info("Subscribed to %s", topics)

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
        topic = message_context.topic()
        partition = message_context.partition()
        this_offset = message_context.offset()

        # see if we've already committed this or a higher offset
        # delivery report from kafka producer are not guaranteed to be in order
        # that they were produced
        # https://github.com/confluentinc/confluent-kafka-python/issues/300#issuecomment-358416432

        try:
            last_commit = self.last_offset[topic][partition]
        except KeyError:
            # first message from this topic-partition
            self.last_offset[topic][partition] = this_offset
            self.c.store_offsets(message_context)
            return
        if this_offset > last_commit:
            self.c.store_offsets(message_context)  # committed according to auto.commit.interval.ms
            self.last_offset[topic][partition] = this_offset

    def on_fail(self, message_context: Message) -> None:
        logger.critical(
            "Downstream failure. Did not commit topic: %s, partition: %d, offset: %d, message: %s.",
            message_context.topic(),
            message_context.partition(),
            message_context.offset(),
            message_context.value(),
        )
        if self.stop_on_failure:
            logger.critical("Downstream failure. Stopping application.")
            # explicitly call the connectors shutdown
            self.shutdown()
            # this send a kill command to py-volley engine to handle any other graceful shutdown procedures
            os.kill(os.getpid(), signal.SIGINT)

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


class BatchJsonConfluentConsumer(ConfluentKafkaConsumer):
    """Consumes multiple messages before process.
    Parses messages to byte string json

    ## Configuration
    You may find yourself wanting to configure a single Volley worker to consume
        and process multiple messages per cycle.
    For example, consume 10 messages for a batch write to a Redis cache.

    Use the batch Kafka Consumer by either specifying `profile`:

    ```python hl_lines="3"
    cfg = {
        "input-topic": {
            "profile": "confluent-batch-json",
            "value": "kafka.topic.0,kafka.topic.1",
            "config": {
                "bootstrap.servers": "kafka:9092",
                "group.id": "myConsumerGroup",
                "batch_size" 10,
                "batch_time_seconds": 2.5,
            },
        },
    }
    ```

    Or by overriding the consumer:

    ```python hl_lines="5"
    cfg = {
        "input-topic": {
            "value": "kafka.topic.0,kafka.topic.1",
            "profile": "confluent",
            "consumer": "volley.connectors.confluent.ConfluentKafkaConsumer",
            "config": {
                "bootstrap.servers": "kafka:9092",
                "group.id": "myConsumerGroup",
                "batch_size" 10,
                "batch_time_seconds": 2.5,
            },
        },
    }
    ```
    Your application then receives a `List` of 10 messages (assuming there were 10 available to be consumed).

    """

    batch_size: int = 5
    batch_time_seconds: float = 2.0

    def __post_init__(self) -> None:
        # handle some configurations before setting ConfluentKafkaConsumer
        if "batch_size" in self.config:
            self.batch_size = self.config.pop("batch_size")
        if "batch_time_seconds" in self.config:
            self.batch_time_seconds = self.config.pop("batch_time_seconds")
        super().__post_init__()

    def consume(
        self,
    ) -> Optional[QueueMessage]:
        """consumes self.config["batch_size"] messages from the input topic
        if self.config["batch_time_seconds"] reached, return however many messages currently consumed
        other wise keep polling for messages until batch_size is reached
        """

        messages: List[Optional[bytes]] = []
        raw_messages: List[Union[Message, None]] = self.c.consume(
            num_messages=self.batch_size, timeout=self.batch_time_seconds
        )
        for_commit: List[Message] = []
        if not len(raw_messages):
            logger.debug("No messages")
            return None
        for m in raw_messages:
            if m is None:
                continue
            elif m.error():
                logger.error(m.error())
                continue
            else:
                for_commit.append(m)
                messages.append(m.value())
        num_messages = len(messages)
        if num_messages:
            logger.debug("messages in batch/batch_size %s / %s", num_messages, self.batch_size)
            all_msg: bytes = b"[" + b",".join(messages) + b"]"  # type: ignore
            return QueueMessage(message_context=for_commit, message=all_msg)
        else:
            return None

    def on_success(self, message_context: List[Message]) -> None:
        """stores any offsets that are able to be stored"""

        # see if we've already committed this or a higher offset
        # delivery report from kafka producer are not guaranteed to be in order
        # that they were produced
        # https://github.com/confluentinc/confluent-kafka-python/issues/300#issuecomment-358416432
        for m in message_context:
            topic = m.topic()
            partition = m.partition()
            this_offset = m.offset()

            try:
                last_commit = self.last_offset[topic][partition]
            except KeyError:
                # first message from this topic-partition
                self.last_offset[topic][partition] = this_offset
                self.c.store_offsets(m)
                continue
            if this_offset > last_commit:
                self.c.store_offsets(m)  # committed according to auto.commit.interval.ms
                self.last_offset[topic][partition] = this_offset
