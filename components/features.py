from typing import Dict

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:
    message.message["features"] = {"feature": "random"}

    return {"triage": message}
