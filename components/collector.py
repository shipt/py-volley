from typing import Any, Dict, List, Tuple

from engine.engine import bundle_engine

INPUT_QUEUE = "collector"
OUTPUT_QUEUES = ["publisher"]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    # TODO: collector should handle determining "event_type"
    return [("publisher", message)]
