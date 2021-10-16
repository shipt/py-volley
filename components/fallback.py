from datetime import datetime
from typing import Dict
from uuid import uuid4

from engine.component import bundle_engine
from engine.data_models import BundleMessage, CollectorMessage

INPUT_QUEUE = "fallback"
OUTPUT_QUEUES = ["collector"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:

    c = CollectorMessage(
        engine_event_id=message.message["engine_event_id"],
        bundle_event_id=message.message["bundle_event_id"],
        fallback_id=str(uuid4()),
        fallback_finish=str(datetime.now()),
        fallback_results={"fallback_solution": "random"},
    )
    message.message = c.fallback_dict()
    return {"collector": message}
