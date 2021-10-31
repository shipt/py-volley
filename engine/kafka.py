import json
from dataclasses import dataclass

from pyshipt_streams import KafkaConsumer, KafkaProducer

from core.logging import logger
from engine.consumer import Consumer
from engine.data_models import QueueMessage
from engine.producer import Producer


@dataclass
class BundleConsumer(Consumer):
    def __post_init__(self) -> None:
        # TODO: config for consumer group..env var maybe?
        self.c = KafkaConsumer(
            consumer_group="group1",
            config_override={"enable.auto.offset.store": False}
        )
        self.c.subscribe([self.queue_name])

    def consume(
        self,
        queue_name: str = None,
        timeout: float = 60,
        poll_interval: float = 0.25,
    ) -> QueueMessage:
        if queue_name is None:
            queue_name = self.queue_name
        message = None
        while message is None:

            message = self.c.poll(poll_interval)
            if message is None:
                continue
            if message.error():
                logger.warning(message.error())
                message = None
                continue
            else:
                msg = json.loads(message.value().decode("utf-8"))
                if msg is None:
                    continue
                else:
                    return QueueMessage(message_id=message, message=msg)

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        self.c.store_offsets(message_id)
        return True

    def on_fail(self) -> None:
        # if we fail on this message - commit the current offset, rather than current + 1
        # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.Consumer.commit
        # https://www.oreilly.com/library/view/kafka-the-definitive/9781491936153/ch04.html
        # self.c.consumer.commit(offsets=STUFF TO COMMMIT)
        pass

    def shutdown(self) -> None:
        self.c.close()


@dataclass
class BundleProducer(Producer):
    def __post_init__(self) -> None:
        self.p = KafkaProducer()

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        value = json.dumps(message.message, default=str).encode("utf-8")
        self.p.publish(topic=queue_name, value=value)
        return True

    def shutdown(self) -> None:
        self.p.flush()