import os
import json


from pyshipt_streams import KafkaConsumer

from components.base import Component, logger
from typing import Any


c = KafkaConsumer(consumer_group="group1")
INPUT_QUEUE = os.environ["INPUT_QUEUE"]
OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]

c.subscribe([INPUT_QUEUE])

class FeatureGenerator(Component):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def process(self, msg: dict[str, Any]) -> dict[str, Any]:
        msg["features"] = {"feature1": 123}
        return msg


comp: FeatureGenerator = FeatureGenerator(qname=OUTPUT_QUEUE)

def main():
    while True:
        message = c.poll(0.25)
        if message is None:
            continue
        if message.error():
            print(message.error())
        else:
            consumed_message = json.loads(message.value().decode("utf-8"))
        processes_msg = comp.process(consumed_message)
        comp.publish(processes_msg)
        logger.info(f"features: {processes_msg}")

