import os
from uuid import uuid4
import time

OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]

from pyshipt_streams import KafkaProducer

p = KafkaProducer()

from components.base import logger

def main():
    while True:
        msg = {
            "event_id": 123,
            "order": str(uuid4()),
            }
        p.publish(
            OUTPUT_QUEUE,
            msg
        )
        logger.info(f"EVENT: {msg}")
        time.sleep(5)
