from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import pandas as pd

from components.data_models import CollectTriage, TriageMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]

OPT_TIMEOUT_SECONDS = 60


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: TriageMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.copy()
    enriched_orders: List[Dict[str, Any]] = in_message.enriched_orders
    # # GROUP ORDERS BY TIME WINDOW
    orders_lst = enriched_orders
    orders = pd.DataFrame(orders_lst)
    orders['TW_HR'] = pd.to_datetime(orders['delivery_start_time']).dt.hour
    orders = orders.sort_values('TW_HR')

    group_df = orders.groupby("TW_HR")
    grouped_orders = [group.to_dict(orient="records") for _,group in group_df]

    t = CollectTriage(
        engine_event_id=message.engine_event_id,
        bundle_request_id=message.bundle_request_id,
        timeout=str(datetime.now() + timedelta(seconds=OPT_TIMEOUT_SECONDS)),
    )

    opt_fall_msg = ComponentMessage(
            engine_event_id=message.engine_event_id,
            bundle_request_id=message.bundle_request_id,
            message=grouped_orders
    )

    return [
        ("optimizer", opt_fall_msg),
        ("fallback", opt_fall_msg),
        ("collector", t),
    ]
