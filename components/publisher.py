from typing import List, Tuple

from components.data_models import OutputMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

# reads from postgres (publisher table)
INPUT_QUEUE = "publisher"
# output to output-queue (kafka topic)
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, OutputMessage]]:
    message = in_message.dict()

    result_set = []

    for m in message["results"]:
        # TODO: data model for results
        if m.get("optimizer_results"):
            name = "optimizer"
            bundled = m["optimizer_results"]["bundles"]
        else:
            name = "fallback"
            bundled = m["fallback_results"]["bundles"]

        pm = OutputMessage(
            engine_event_id=m["engine_event_id"],
            bundle_event_id=m["bundle_event_id"],
            bundles=bundled,
            optimizer_type=name,
        )

        result_set.append(("output-queue", pm))
    return result_set
