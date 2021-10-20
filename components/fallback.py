from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from components.data_models import CollectorMessage
from engine.component import bundle_engine
from engine.data_models import QueueMessage

INPUT_QUEUE = "fallback"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: QueueMessage) -> List[Tuple[str, QueueMessage]]:

    falback_solution = {
        "bundles": ["order_1", "order2", "order_5", "order3"],
        "other_data": "abc",
    }
    c = CollectorMessage(
        engine_event_id=message.message["engine_event_id"],
        bundle_event_id=message.message["bundle_event_id"],
        fallback_id=str(uuid4()),
        fallback_finish=str(datetime.now()),
        fallback_results=falback_solution,
    )
    message.message = c.fallback_dict()
    return [("collector", message)]
