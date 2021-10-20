from datetime import datetime, timedelta
from typing import List, Tuple

from components.data_models import CollectorMessage
from engine.engine import bundle_engine
from engine.data_models import QueueMessage

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: QueueMessage) -> List[Tuple[str, QueueMessage]]:
    opt_message = message.copy()
    opt_message.message["triage"] = {"triage": ["a", "b"]}

    c = CollectorMessage(
        engine_event_id=message.message["engine_event_id"],
        bundle_event_id=message.message["bundle_event_id"],
        store_id=message.message["store_id"],
        timeout=str(datetime.now() + timedelta(minutes=5)),
    )
    message.message = c.dict()
    message.message["event_type"] = "triage"
    return [
        ("optimizer", opt_message),
        ("fallback", opt_message),
        ("collector", message),
    ]
