import json

from pyshipt_streams import KafkaConsumer

from engine.logging import logger
from engine.queues import available_queues


def main() -> None:
    queues = available_queues()
    input_topic = queues.queues["output-queue"].value
    c = KafkaConsumer(consumer_group="group1")
    c.subscribe([input_topic])

    while True:
        message = c.poll(0.25)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_message = json.loads(message.value().decode("utf-8"))

            logger.info(consumed_message)
