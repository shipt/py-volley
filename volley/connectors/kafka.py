import os
import sys
from dataclasses import dataclass
from typing import Optional

from pyshipt_streams import KafkaConsumer as KConsumer
from pyshipt_streams import KafkaProducer as KProducer

from volley.config import APP_ENV
from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage
from volley.logging import logger

RUN_ONCE = False


@dataclass
class KafkaConsumer(Consumer):
    def __post_init__(self) -> None:
        self.host = os.environ["KAFKA_BROKERS"]

        # consumer group assignment
        # use env var first, then command line argument w/ env, then auto generate one
        try:
            consumer_group = os.environ["KAFKA_CONSUMER_GROUP"]
        except KeyError:
            # TODO: need a better way to do this
            # keeping to prevent breaking change
            logger.warning("KAFKA_CONSUMER_GROUP not specified in environment")
            try:
                component_name = sys.argv[1]
                consumer_group = f"{APP_ENV}_{component_name}"
            except KeyError:
                logger.exception("Kafka Consumer group not specified")

        logger.info(f"Kafka {consumer_group=}")
        self.consumer_group: str = consumer_group
        self.c = KConsumer(
            consumer_group=consumer_group,
            # TODO: develop commit strategy to minimize duplicates and guarantee no loss
            # config_override={"enable.auto.offset.store": False}
        )
        logger.info(f"Kafka Config: {self.c.config}")
        self.c.subscribe([self.queue_name])

    def consume(  # type: ignore
        self,
        queue_name: str = None,
        timeout: float = 60,
        poll_interval: float = 0.25,
    ) -> Optional[QueueMessage]:
        if queue_name is None:
            queue_name = self.queue_name

        message = self.c.poll(poll_interval)
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
    def __post_init__(self) -> None:
        self.host = os.environ["KAFKA_BROKERS"]
        self.p = KProducer()
        logger.info(f"Kafka Config: {self.p.config}")

    def produce(self, queue_name: str, message: bytes) -> bool:
        self.p.publish(topic=queue_name, value=message)
        return True

    def shutdown(self) -> None:
        self.p.flush()
