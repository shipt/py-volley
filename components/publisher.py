import time
from datetime import datetime
from typing import Dict
from uuid import uuid4

from engine.component import bundle_engine
from engine.data_models import BundleMessage, PublisherMessage

INPUT_QUEUE = "publisher"
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:

    m = PublisherMessage(
        engine_event_id=message.message["engine_event_id"],
        bundle_event_id=message.message["bundle_event_id"],
        store_id=message.message["store_id"],
        bundles=[],
    )
    return {"output-queue": message}
