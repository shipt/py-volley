from typing import Dict
from uuid import uuid4

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> Dict[str, BundleMessage]:
    message.message["features"] = {"feature": "random"}
    message.message["engine_event_id"] = str(uuid4())
    return {"triage": message}
