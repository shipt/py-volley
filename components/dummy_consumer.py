import json
import os

from pyshipt_streams import KafkaConsumer

from core.logging import logger


def main() -> None:
    INPUT_QUEUE = os.environ["INPUT_QUEUE"]
    c = KafkaConsumer(consumer_group="group1")
    c.subscribe([INPUT_QUEUE])

    while True:
        message = c.poll(0.25)
        if message is None:
            continue
        if message.error():
            logger.error(message.error())
        else:
            consumed_message = json.loads(message.value().decode("utf-8"))

            for key in ["features", "triage", "optimizer", "collector"]:
                assert key in consumed_message.keys()
            logger.info(f"## WIN!:  {consumed_message} ##")
