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
        self.c = KafkaConsumer(consumer_group="group1")
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
                logger.info(message.error())
            else:
                msg = json.loads(message.value().decode("utf-8"))
                if msg is None:
                    continue
                else:
                    return QueueMessage(message_id=str(message.offset()), message=msg)

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        # TODO: should we hard-commit here?
        print("no message to delete!")
        return True

    def on_fail(self) -> None:
        pass


@dataclass
class BundleProducer(Producer):
    def __post_init__(self) -> None:
        self.p = KafkaProducer()

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        self.p.publish(topic=queue_name, value=message.dict()["message"])
        return True
