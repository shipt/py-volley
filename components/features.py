import os
from typing import List, Tuple
from uuid import uuid4

import requests
import rollbar

from components.data_models import InputMessage, TriageMessage
from core.logging import logger
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]
FLIGHT_PLAN_URL = {
    "localhost": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "staging": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "production": "https://flight-plan-service.us-east-1.shipt.com/v1/orders",
}[os.getenv("APP_ENV", "localhost")]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: InputMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()

    raw_orders = []
    enriched_orders = []
    # iterate over keys (order id)
    for order in message["orders"]:
        resp = requests.get(f"{FLIGHT_PLAN_URL}/{order}")
        if resp.status_code == 200:
            try:
                fp_data = resp.json()
                geo_data = {}
                stops = fp_data["route"]["stops"]
                for i, stop in enumerate(fp_data["route"]["stops"]):
                    if i > 1:
                        logger.warning(f"More than one pick one drop in order: {stops}")
                    stop_type = stop["type"]  # pickup or delivery

                    geo_data[stop_type] = {"latitude": stop["latitude"], "longitude": stop["longitude"]}
                store_id = fp_data["order"]["store_id"]
                enriched_orders.append(
                    {
                        "order_id": order,
                        "shop_time_minutes": fp_data["before_claim"]["shop"]["minutes"],
                        "item_qty": len(fp_data["order"]["order_lines"]),
                        "delivery_start_time": fp_data["before_claim"]["delivery"]["starts_at"],
                        "delivery_end_time": fp_data["before_claim"]["delivery"]["ends_at"],
                        "store_name": f"store_id_{store_id}",  # TODO: need store name in Milestone 2
                        "delv_longitude": geo_data["delivery"]["longitude"],
                        "delv_latitude": geo_data["delivery"]["latitude"],
                        "store_longitude": geo_data["pickup"]["longitude"],
                        "store_latitude": geo_data["pickup"]["latitude"],
                    }
                )
            except KeyError:
                logger.exception(f"Flight-plan data missing for order: {order}")
                raw_orders.append(
                    {
                        "order_id": order,
                    }
                )
        else:
            logger.warning(f"Flight-plan returned status code: {resp.status_code} for order: {order}")
            raw_orders.append(
                {
                    "order_id": order,
                }
            )

    output_message = TriageMessage(
        raw_orders=raw_orders,
        enriched_orders=enriched_orders,
        bundle_request_id=message["bundle_request_id"],
        engine_event_id=str(uuid4()),
    )
    return [("triage", output_message)]
