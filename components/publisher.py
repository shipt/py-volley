from typing import List, Tuple

from engine.component import bundle_engine
from engine.data_models import BundleMessage, OutputMessage

INPUT_QUEUE = "publisher"
OUTPUT_QUEUES = ["output-queue"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> List[Tuple[str, BundleMessage]]:
    result_set = []
    for m in message.message["results"]:
        # TODO: data model for results
        if m["optimizer_results"]:
            name = "optimizer"
            bundled = m["optimizer_results"]["bundles"]
        else:
            name = "fallback"
            bundled = m["fallback_results"]["bundles"]

        pm = OutputMessage(
            engine_event_id=m["engine_event_id"],
            bundle_event_id=m["bundle_event_id"],
            store_id=m["store_id"],
            bundles=bundled,
            optimizer_type=name,
        )

        bm = message.copy()
        bm.message = pm.dict()

        result_set.append(("output-queue", bm))
    return result_set
