import time
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from components.data_models import CollectorMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:

    # TODO: data model for opt results
    opt_solution = {
        "bundles": ["order_1", "order2", "order_5", "order3"],
        "other_data": "abc",
    }

    c = CollectorMessage(
        engine_event_id=message["engine_event_id"],
        bundle_event_id=message["bundle_event_id"],
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results=opt_solution,
    )
    message = c.optimizer_dict()

    # artificially longer optimizer than other components
    time.sleep(10)
    return [("collector", message)]
