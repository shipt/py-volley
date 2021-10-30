from datetime import datetime, timedelta
from typing import List, Tuple

from components.data_models import CollectTriage, TriageMessage
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "triage"
OUTPUT_QUEUES = ["optimizer", "fallback", "collector"]  # , "shadow"]

OPT_TIMEOUT_SECONDS = 60


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: TriageMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.copy()
    message.message["triage"] = {"triage": ["a", "b"]}

    # # GROUP ORDERS BY TIME WINDOW
    # order_lst = message.message.get("order_list")
    # orders = pd.concat(orders_lst)
    # orders['TW_HR'] = pd.to_datetime(orders['delivery_start_time']).dt.hour
    # orders = orders.sort_values('TW_HR')
    # grouped_orders = []
    # for hours in orders['TW_HR']:
    #     orders = orders[orders['TW_HR'] == hours]
    #     grouped_orders.append(orders)

    t = CollectTriage(
        engine_event_id=message["engine_event_id"],
        bundle_request_id=message["bundle_request_id"],
        timeout=str(datetime.now() + timedelta(seconds=OPT_TIMEOUT_SECONDS)),
    )

    return [
        ("optimizer", in_message),
        ("fallback", in_message),
        ("collector", t),
    ]
