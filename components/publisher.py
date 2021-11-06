from datetime import datetime
from typing import List, Tuple

import pytz

from components.data_models import OutputMessage, PublisherMessage
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
def main(in_message: PublisherMessage) -> List[Tuple[str, OutputMessage]]:
    message = in_message.dict()

    result_set = []

    for m in message["results"]:
        engine_event_id = m["engine_event_id"]
        bundle_request_id = m["bundle_request_id"]

        if m.get("optimizer_results"):
            optimizer_type = "optimizer"
            bundled = m["optimizer_results"]["bundles"]
        elif m.get("fallback_results"):
            optimizer_type = "fallback"
            bundled = m["fallback_results"]["bundles"]
        else:
            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            if now < m["timeout"]:
                continue
            else:
                msg = f"{engine_event_id=} - {bundle_request_id} expired without results"
                logger.error(msg)
                raise TimeoutError(msg)
                

        pm = OutputMessage(
            engine_event_id=m["engine_event_id"],
            bundle_request_id=m["bundle_request_id"],
            bundles=bundled,
            optimizer_type=optimizer_type,
        )
        logger.info(f"{optimizer_type=}")

        result_set.append(("output-queue", pm))
    return result_set
