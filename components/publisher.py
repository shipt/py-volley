from datetime import datetime
from typing import List, Optional, Tuple

import pytz
from prometheus_client import Counter

from components.data_models import OutputMessage, PublisherMessage
from engine.engine import bundle_engine
from engine.logging import logger

# reads from postgres (publisher table)
INPUT_QUEUE = "publisher"
# output to output-queue (kafka topic)
OUTPUT_QUEUES = ["output-queue"]


SOLUTION_TYPE = Counter("solution", "Count of solution by type", ["type"])  # fallback or optimizer


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: PublisherMessage) -> List[Tuple[str, Optional[OutputMessage]]]:
    message = in_message.dict()

    result_set: List[Tuple[str, Optional[OutputMessage]]] = []

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
            if now < m["timeout"].replace(tzinfo=pytz.UTC):
                continue
            else:
                msg = f"{engine_event_id=} - {bundle_request_id} expired without results"
                logger.error(msg)
                result_set.append(("output-queue", None))
                continue

        pm = OutputMessage(
            engine_event_id=m["engine_event_id"],
            bundle_request_id=m["bundle_request_id"],
            bundles=bundled,
            optimizer_type=optimizer_type,
        )
        SOLUTION_TYPE.labels(optimizer_type).inc()
        logger.info(f"{optimizer_type=}")

        result_set.append(("output-queue", pm))
    return result_set
