from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import pandas as pd

from components.data_models import CollectTriage, OptimizerMessage, TriageMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine
from engine.logging import logger

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]

OPT_TIMEOUT_SECONDS = 120


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: TriageMessage) -> List[Tuple[str, ComponentMessage]]:

    enriched_orders: List[Dict[str, Any]] = [x.dict() for x in in_message.enriched_orders]

    grouped_orders = []
    if enriched_orders:
        # # GROUP ORDERS BY TIME WINDOW
        orders = pd.DataFrame(enriched_orders)
        orders["TW_HR"] = pd.to_datetime(orders["delivery_start_time"]).dt.hour
        orders = orders.sort_values("TW_HR")

        group_df = orders.groupby("TW_HR")
        grouped_orders = [group.to_dict(orient="records") for _, group in group_df]
    else:
        logger.info(f"No enriched orders for bundle_request_id={in_message.bundle_request_id}")

    t = CollectTriage(
        engine_event_id=in_message.engine_event_id,
        bundle_request_id=in_message.bundle_request_id,
        timeout=str(datetime.utcnow() + timedelta(seconds=OPT_TIMEOUT_SECONDS)),
    )

    opt_fall_msg = OptimizerMessage(
        engine_event_id=in_message.engine_event_id,
        bundle_request_id=in_message.bundle_request_id,
        grouped_orders=grouped_orders,
        error_orders=in_message.error_orders,
    )

    return [
        ("optimizer", opt_fall_msg),
        ("fallback", opt_fall_msg),
        ("collector", t),
    ]
