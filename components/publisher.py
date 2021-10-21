from typing import Any, Dict, List, Tuple

from components.data_models import OutputMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "publisher"
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
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

        result_set.append(("output-queue", pm.dict()))
    return result_set
