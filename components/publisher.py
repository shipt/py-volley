import time
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from engine.component import bundle_engine
from engine.data_models import BundleMessage, OutputMessage

INPUT_QUEUE = "publisher"
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> List[Tuple[str, BundleMessage]]:
    bundled_orders: List[Dict[str, Any]] = message.message["bundles"]
    result_set = []
    for m in message.message["results"]:

        pm = OutputMessage(
            engine_event_id=message.message["engine_event_id"],
            bundle_event_id=message.message["bundle_event_id"],
            store_id=message.message["store_id"],
            bundles=[],
        )

        bm = message.copy()
        bm.message = pm.dict()

        result_set.append(("output-queue", bm))
        # multiple keys of same name?
        # single key but list of messages to publish to that queue?
        # ^ would require procuder to take in a list by default...might be good to do it this way

    return result_set
