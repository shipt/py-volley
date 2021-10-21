from typing import List, Tuple

from components.data_models import PublisherInput
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "collector"
OUTPUT_QUEUES = ["publisher"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()

    p = PublisherInput(**message)
    # TODO: collector should handle determining "event_type"? instead of postgres producer
    return [("publisher", p)]
