import json
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
        with open("./seed/fp_payload.json", "r") as file:
            data = json.load(file)
        msg = {
            "bundle_event_id": i,
            "store_id": str(uuid4()),
            "orders": [data],
        }
        p.publish(input_topic, msg)
        logger.info(f"{msg=}")
        time.sleep(10)
        i += 1
