import os

from components.base import Component
from typing import Any
from core.logging import logger

INPUT_QUEUE = os.environ["INPUT_QUEUE"]
OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]

class Triage(Component):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def process(self, msg: dict[str, Any]) -> dict[str, Any]:
        message = msg["message"]
        message["triage_data"] = ["a", "b", "c"]
        return message

def main():
    input_comp: Triage = Triage(qname=INPUT_QUEUE)
    output_comp: Triage = Triage(qname=OUTPUT_QUEUE)

    while True:
        msg = input_comp.consume()
        processes_msg = input_comp.process(msg)
        output_comp.publish(processes_msg)
        logger.info(f"triage: {processes_msg}")
        input_comp.delete_msg(msg)