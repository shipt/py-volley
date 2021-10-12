from typing import Tuple

import numpy as np

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["triage", "collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Tuple[BundleMessage, str]:
    message.message["optimizer"] = {"result": ["a", "b"]}

    next_queue = np.random.choice(OUTPUT_QUEUES)
    return message, next_queue
