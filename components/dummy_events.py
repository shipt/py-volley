import time

from pyshipt_streams import KafkaProducer

from components.data_models import InputMessage
from core.logging import logger
from engine.queues import available_queues


def main() -> None:
    queues = available_queues()
    input_topic = queues.queues["input-queue"].value
    logger.info(f"{input_topic=}")
    p = KafkaProducer()
    i = 0
    while True:
        data = InputMessage.schema()["examples"][0]
        p.publish(input_topic, data)
        logger.info(f"{data=}")
        time.sleep(10)
        i += 1
