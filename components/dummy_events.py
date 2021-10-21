import json
import time

from pyshipt_streams import KafkaProducer

from core.logging import logger
from engine.queues import available_queues


def main() -> None:
    queues = available_queues()
    input_topic = queues.queues["input-queue"].value
    logger.info(f"{input_topic=}")
    p = KafkaProducer()
    i = 0
    while True:
        with open("./seed/input_message.json", "r") as file:
            data = json.load(file)
        p.publish(input_topic, data)
        logger.info(f"{data=}")
        time.sleep(10)
        i += 1
