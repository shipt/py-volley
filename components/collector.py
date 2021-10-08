from pyshipt_streams import KafkaProducer

import os
from components.base import Component
from typing import Any


INPUT_QUEUE = os.environ["INPUT_QUEUE"]
OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]

class Collector(Component):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def process(self, msg: dict[str, Any]) -> dict[str, Any]:
        message = msg["message"]
        message["collector_data"] = {"collector": 123}
        return message




def main():
    input_comp: Collector = Collector(qname=INPUT_QUEUE)

    p = KafkaProducer()

    while True:
        try:
            msg = input_comp.consume()
        except Exception:
            continue
        processes_msg = input_comp.process(msg)
        p.publish(topic=OUTPUT_QUEUE, value=processes_msg)
        input_comp.delete_msg(msg)
