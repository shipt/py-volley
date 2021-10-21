from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

from components.data_models import CollectorMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: Dict[str, Any]) -> List[Tuple[str, Union[Dict[str, Any], ComponentMessage]]]:
    opt_message = message.copy()
    message["triage"] = {"triage": ["a", "b"]}

    c = CollectorMessage(
        engine_event_id=message["engine_event_id"],
        bundle_event_id=message["bundle_event_id"],
        store_id=message["store_id"],
        timeout=str(datetime.now() + timedelta(minutes=5)),
    )
    c_message = c.dict()
    c_message["event_type"] = "triage"
    return [
        ("optimizer", opt_message),
        ("fallback", opt_message),
        ("collector", message),
    ]


# message = {
#     "engine_event_id": "abc",
#     "bundle_event_id": "abc123",
#     "store_id": "store_a",
# }
