import json
import sys
from dataclasses import dataclass

from pyshipt_streams import KafkaConsumer as KConsumer
from pyshipt_streams import KafkaProducer as KProducer

from engine.connectors.base import Consumer, Producer
from engine.data_models import QueueMessage
from engine.logging import logger

RUN_ONCE = False


@dataclass
class KafkaConsumer(Consumer):
    def __post_init__(self) -> None:
        try:
            # TODO: client implementing this consumer should be able to specify its consumer group
            # for now, we'll try to use the name of the component in the consumer group
            component_name = sys.argv[1]
        except:
            component_name = "bundle_engine"

        self.c = KConsumer(
            consumer_group=f"{component_name}_consumer",
            # TODO: develop commit strategy to minimize duplicates and guarantee no loss
            # config_override={"enable.auto.offset.store": False}
        )
        self.c.subscribe([self.queue_name])

    def consume(  # type: ignore
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
                pass
            elif message.error():
                logger.warning(message.error())
                message = None
            else:
                msg = json.loads(message.value().decode("utf-8"))
                if msg is None:
                    continue
                else:
                    return QueueMessage(message_id=message, message=msg)
            if RUN_ONCE:
                # for testing purposes only - mock RUN_ONCE
                break

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
        self.p = KProducer()

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        value = json.dumps(message.message, default=str).encode("utf-8")
        self.p.publish(topic=queue_name, value=value)
        return True

    def shutdown(self) -> None:
        self.p.flush()
