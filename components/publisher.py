from datetime import datetime
from typing import List, Tuple

from components.data_models import OutputMessage
from core.logging import logger
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

# reads from postgres (publisher table)
INPUT_QUEUE = "publisher"
# output to output-queue (kafka topic)
OUTPUT_QUEUES = ["output-queue"]


class TimeoutError(Exception):
    pass


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, OutputMessage]]:
    message = in_message.dict()

    result_set = []

    for m in message["results"]:
        engine_event_id = m["engine_event_id"]
        bundle_request_id = m["bundle_event_id"]

        if m.get("optimizer_results"):
            name = "optimizer"
            bundled = m["optimizer_results"]["bundles"]
        elif m.get("fallback_results"):
            name = "fallback"
            bundled = m["fallback_results"]["bundles"]
        else:
            now = datetime.now()
            if now > m["timeout"]:
                msg = f"{engine_event_id=} - {bundle_request_id} expired without results"
                logger.error(msg)
                raise TimeoutError(msg)

        pm = OutputMessage(
            engine_event_id=m["engine_event_id"],
            bundle_event_id=m["bundle_event_id"],
            bundles=bundled,
            optimizer_type=name,
        )

        result_set.append(("output-queue", pm))
    return result_set
