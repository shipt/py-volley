from dataclasses import dataclass
import json
import time
from typing import Any, Dict

from pyshipt_streams import KafkaProducer, KafkaConsumer

from engine.data_models import BundleMessage
from engine.consumer import Consumer
from engine.producer import Producer

from core.logging import logger


@dataclass
class BundleConsumer(Consumer):

    def __post_init__(self) -> None:
        self.c = KafkaConsumer(consumer_group="group1")
        self.c.subscribe([self.queue_name])

    def consume(self, queue_name: str=None, timeout: float=60, poll_interval: float=0.25) -> BundleMessage:
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
                    return BundleMessage(
                        message_id=str(message.offset()),
                        params={},
                        message=msg
                    )

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        # TODO: should we hard-commit here?
        print("no message to delete!")
        return True

@dataclass
class BundleProducer(Producer):

    def __post_init__(self) -> None:
        self.p = KafkaProducer()

    def produce(self, queue_name: str, message: Dict[str, Any]) -> bool:
        logger.info(f"{queue_name=}")
        self.p.publish(
            topic=queue_name,
            value=message["message"]
        )
        return True
