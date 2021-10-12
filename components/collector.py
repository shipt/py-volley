from typing import Tuple

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "collector"
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Tuple[BundleMessage, str]:
    message.message["collector"] = "collected"

    next_queue = OUTPUT_QUEUES[0]
    return message, next_queue
