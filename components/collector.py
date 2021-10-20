from typing import List, Tuple

from engine.component import bundle_engine
from engine.data_models import QueueMessage

INPUT_QUEUE = "collector"
OUTPUT_QUEUES = ["publisher"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: QueueMessage) -> List[Tuple[str, QueueMessage]]:
    # message.message["collector"] = "collected"
    return [("publisher", message)]
