import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import requests
from pydantic import ValidationError

from components.data_models import EnrichedOrder, InputMessage, TriageMessage
from core.logging import logger
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

APP_ENV = os.getenv("APP_ENV", "localhost")

FP_CALL_WORKERS: int = int(os.getenv("FP_CALL_WORKERS", 10))

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]

METRO_URL = {
    "localhost": "https://shipt-metropolis.us-east-1.staging.shipt.com/v1/configuration/context",
    "staging": "https://shipt-metropolis.us-east-1.staging.shipt.com/v1/configuration/context",
    "production": "https://shipt-metropolis.us-east-1.shipt.com/v1/configuration/context",
}[APP_ENV]


FLIGHT_PLAN_URL = {
    "localhost": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "staging": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "production": "https://flight-plan-service.us-east-1.shipt.com/v1/orders",
}[APP_ENV]


# stores geo data for all location ids
# each request __should__ be for a single location, however
# this is effectively caching the locations lat/long
ALL_METRO_RESULTS: Dict[str, Any] = {}


def get_shop_time(order_id: str) -> Optional[Tuple[str, float]]:
    """Calls flight-plan-service to retrieve shop time

    On success - returns Tuple[order_id: str, shop_time: float]
    On failure - returns None. Logs exception or non-200 response to Rollbar
    """
    resp = requests.get(f"{FLIGHT_PLAN_URL}/{order_id}")

    if resp.status_code == 200:
        try:
            return order_id, resp.json()["before_claim"]["shop"]["minutes"]
        except KeyError:
            logger.exception(f"Flight-plan data missing for order: {order_id}")
    else:
        logger.error(f"Flight-plan returned status code: {resp.status_code} for order: {order_id}")
    return None


def get_shop_time_pooled(order_ids: List[str]) -> Dict[str, float]:
    """concurrently calls get_shop_time (flight-plan-service) for a list of order ids

    Returns a dictionary:
        keys - order_id: str
        value - shop_time: float
    """
    with ThreadPoolExecutor(max_workers=FP_CALL_WORKERS) as executor:
        tasks = [executor.submit(get_shop_time, o) for o in order_ids]

        results = {}
        for t in tasks:
            order_shop_time: Optional[Tuple[str, float]] = t.result()
            if order_shop_time:
                results[order_shop_time[0]] = order_shop_time[1]
        return results


def get_metro_attr(
    store_location_id: str, attributes: List[str] = ["store_location_latitude", "store_location_longitude"]
) -> Dict[str, Any]:
    resp = requests.get(METRO_URL, params={"store_location_id": store_location_id})
    if resp.status_code == 200:
        try:
            body = resp.json()["configuration"]
            results = {attr: body[attr] for attr in attributes}
            results["store_latitude"] = results.pop("store_location_latitude")
            results["store_longitude"] = results.pop("store_location_longitude")
            return results
        except KeyError:
            logger.exception(f"attribute missing from metropolis call: {store_location_id=}")
            return {}
    else:
        logger.error(f"Metro-service returned status code: {resp.status_code} for {store_location_id=}")
        return {}


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: InputMessage) -> List[Tuple[str, Optional[ComponentMessage]]]:
    message = in_message.dict()
    request_id = message["bundle_request_id"]

    error_orders = []
    enriched_orders = []

    all_order_ids = [o["order_id"] for o in message["orders"]]

    # call FP concurrently
    fp_results: Dict[str, float] = get_shop_time_pooled(all_order_ids)

    for order in message["orders"]:
        order_id = order["order_id"]
        # handle geo enrichment
        # only call metro service if we dont already have the data cached
        store_location_id = str(order["store_location_id"])
        if not (metro_results := ALL_METRO_RESULTS.get(store_location_id)):
            metro_results = get_metro_attr(store_location_id=store_location_id)
            ALL_METRO_RESULTS[store_location_id] = metro_results
        order.update(metro_results)

        # handle shop time
        shop_time = fp_results.get(order_id)
        if shop_time:
            order["shop_time_minutes"] = shop_time

        try:
            # EnrichedOrder validation will fail if attributes are missing
            # e.g. FP call fails, shop_time_minutes will not exist. Validation fails.
            enriched_orders.append(EnrichedOrder(**order))
        except ValidationError:
            logger.exception(f"failed enriching {order_id=}")
            # error orders end up getting "bundled as order of one" in Optimizer component
            error_orders.append(order)

    if not any([error_orders, enriched_orders]):
        logger.error(f"NO VALID ORDER: {message}")
        return [("None", None)]

    output_message = TriageMessage(
        error_orders=error_orders,
        enriched_orders=enriched_orders,
        bundle_request_id=request_id,
        engine_event_id=str(uuid4()),
    )
    return [("triage", output_message)]
