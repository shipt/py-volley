import os

import json

INPUT_QUEUE = os.environ["INPUT_QUEUE"]
from core.logging import logger
from pyshipt_streams import KafkaConsumer

c = KafkaConsumer(consumer_group="group1")
c.subscribe([INPUT_QUEUE])

def main():
    while True:
        message = c.poll(0.25)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_message = json.loads(message.value().decode("utf-8"))
            logger.info(f"## WIN!:  {consumed_message} ##")