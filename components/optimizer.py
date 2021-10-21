import time
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from components.data_models import CollectOptimizer
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()

    # TODO: data model for opt results
    opt_solution = {
        "bundles": ["order_1", "order2", "order_5", "order3"],
        "other_data": "abc",
    }

    c = CollectOptimizer(
        engine_event_id=message["engine_event_id"],
        bundle_event_id=message["bundle_event_id"],
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results=opt_solution,
    )

    # artificially longer optimizer than other components
    # remove when we implement this component
    time.sleep(2)
    return [("collector", c)]
