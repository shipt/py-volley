import time
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from engine.component import bundle_engine
from engine.data_models import BundleMessage, CollectorMessage

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> List[Tuple[str, BundleMessage]]:
    c = CollectorMessage(
        engine_event_id=message.message["engine_event_id"],
        bundle_event_id=message.message["bundle_event_id"],
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results={"optimizer_solution": "random"},
    )
    message.message = c.optimizer_dict()

    # artificially longer optimizer than other components
    time.sleep(10)
    return [("collector", message)]
