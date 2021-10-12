import time
from uuid import uuid4

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
        msg = {
            "event_id": i,
            "order": str(uuid4()),
        }
        p.publish(input_topic, msg)
        logger.info(f"{msg=}")
        time.sleep(10)
        i += 1
