from datetime import datetime, timedelta
from typing import List, Tuple

from components.data_models import CollectTriage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()

    in_message.triage = {"triage": ["a", "b"]}  # type: ignore

    t = CollectTriage(
        engine_event_id=message["engine_event_id"],
        bundle_event_id=message["bundle_event_id"],
        timeout=str(datetime.now() + timedelta(minutes=5)),
    )

    return [
        ("optimizer", in_message),
        ("fallback", in_message),
        ("collector", t),
    ]
