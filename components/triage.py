from typing import Tuple

import numpy as np

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback"]  # , "shadow"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Tuple[BundleMessage, str]:
    message.message["triage"] = {"triage": ["a", "b"]}

    next_queue = np.random.choice(OUTPUT_QUEUES)
    return message, next_queue
