from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from components.data_models import CollectFallback, OptimizerMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "fallback"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: OptimizerMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()

    falback_solution = {
        "bundles": [
            {"group_id": "g1234", "orders": ["order_1", "order2", "order_4"]},
            {"group_id": "g1235", "orders": ["order_3"]},
        ]
    }
    c = CollectFallback(
        engine_event_id=message["engine_event_id"],
        bundle_request_id=message["bundle_request_id"],
        fallback_id=str(uuid4()),
        fallback_finish=str(datetime.now()),
        fallback_results=falback_solution,
    )

    return [("collector", c)]
