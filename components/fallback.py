from typing import Dict

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "fallback"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:
    message.message["fallback"] = {"fallback_solution": "random"}

    return {"collector": message}
