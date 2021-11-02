import os
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import requests

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


def validate_geo_data(geo_data: Dict[str, Any]) -> None:
    for stop_type, latlon in geo_data.items():
        longitude = latlon["longitude"]
        latitude = latlon["latitude"]
        if longitude == 0 and latitude == 0:
            logger.error(f"invalid {longitude=} {latitude=}")
        # northern hemisphere?
        if longitude is None or longitude < -180 or longitude > -50:
            logger.error(f"invalid {longitude=}")

        # western hemisphere?
        if latitude is None or latitude < -10 or latitude > 90:
            logger.error(f"invalid {latitude=}")


def handle_fp_call(order_id: str) -> Tuple[Dict[str, Any], bool]:
    resp = requests.get(f"{FLIGHT_PLAN_URL}/{order_id}")
    if resp.status_code == 200:
        try:
            fp_data = resp.json()
            geo_data = {}
            stops = fp_data["route"]["stops"]
            for i, stop in enumerate(stops):
                if i > 1:
                    logger.error(f"More than one pick one drop in order: {stops}")
                stop_type = stop["type"]  # pickup or delivery

                geo_data[stop_type] = {"latitude": stop["latitude"], "longitude": stop["longitude"]}
            validate_geo_data(geo_data)
            store_id = fp_data["order"]["store_id"]
            return {
                "order_id": order_id,
                "shop_time_minutes": fp_data["before_claim"]["shop"]["minutes"],
                "item_qty": len(fp_data["order"]["order_lines"]),
                "delivery_start_time": fp_data["before_claim"]["delivery"]["starts_at"],
                "delivery_end_time": fp_data["before_claim"]["delivery"]["ends_at"],
                "store_name": f"store_id_{store_id}",  # TODO: need store name in Milestone 2
                "delv_longitude": geo_data["delivery"]["longitude"],
                "delv_latitude": geo_data["delivery"]["latitude"],
                "store_longitude": geo_data["pickup"]["longitude"],
                "store_latitude": geo_data["pickup"]["latitude"],
            }, True
        except KeyError:
            logger.exception(f"Flight-plan data missing for order: {order_id}")
    else:
        logger.error(f"Flight-plan returned status code: {resp.status_code} for order: {order_id}")

    # either non-200 or KeyError
    return {"order_id": order_id}, False


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: InputMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()
    logger.info(f"{FLIGHT_PLAN_URL=}")
    raw_orders = []
    enriched_orders = []
    # iterate over keys (order id)
    for order in message["orders"]:
        result, status = handle_fp_call(order)
        if status:
            enriched_orders.append(result)
        else:
            raw_orders.append(result)

    output_message = TriageMessage(
        error_orders=raw_orders,
        enriched_orders=enriched_orders,
        bundle_request_id=message["bundle_request_id"],
        engine_event_id=str(uuid4()),
    )
    return [("triage", output_message)]
