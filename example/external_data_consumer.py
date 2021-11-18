import json
from typing import Dict

from pyshipt_streams import KafkaConsumer

from volley.logging import logger
from volley.queues import Queue, available_queues


def main() -> None:
    queues: Dict[str, Queue] = available_queues()
    input_topic = queues["output-queue"].value
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
