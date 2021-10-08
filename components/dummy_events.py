import os
import time
from uuid import uuid4

OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]

from pyshipt_streams import KafkaProducer

p = KafkaProducer()

from core.logging import logger


def main():
    i = 0
    while True:
        msg = {
            "event_id": i,
            "order": str(uuid4()),
        }
        p.publish(OUTPUT_QUEUE, msg)
        logger.info(f"EVENT: {msg}")
        time.sleep(10)
        i += 1
