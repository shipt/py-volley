from typing import Dict

import numpy as np

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["triage", "collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:
    message.message["optimizer"] = {"result": ["a", "b"]}

    if np.random.choice([0, 1]):
        _next = {"collector": message}
    else:
        _next = {"triage": message}
    return _next
