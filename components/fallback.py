import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import pandas as pd
import requests

from components.data_models import CollectFallback, OptimizerMessage
from engine.config import ENV
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine
from engine.logging import logger

INPUT_QUEUE = "fallback"
OUTPUT_QUEUES = ["collector"]
FALLBACK_URL = {
    "localhost": "https://ds-bundling-fallback.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "staging": "https://ds-bundling-fallback.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "production": "https://ds-bundling-fallback.ds.us-central1.shipt.com/v1/bundle/optimize",
}[ENV]


def handle_fallback_call(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    order_list = []
    for order in body["order_list"]:
        order["delivery_start_time"] = pd.to_datetime(order["delivery_start_time"]).isoformat()
        order["delivery_end_time"] = pd.to_datetime(order["delivery_end_time"]).isoformat()
        order["item_qty"] = order.pop("total_items")
        order["store_name"] = "TODO"
        order_list.append(order)

    body["order_list"] = order_list
    resp = requests.post(FALLBACK_URL, data=json.dumps(body, default=str))
    if resp.status_code == 200:
        bundles: List[Dict[str, Any]] = resp.json()["bundles"]
    else:
        logger.error(f"{FALLBACK_URL} - {resp.status_code=} - {body=}")
        # create bundles of 1
        bundles = []
        for o in body["order_list"]:
            bundles.append({"group_id": str(uuid4()), "orders": [o["order_id"]]})
    return bundles


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: OptimizerMessage) -> List[Tuple[str, ComponentMessage]]:
    """handle calling the optimization service"""
    message = in_message.dict()
    bundles: List[Dict[str, Any]] = []

    if message["grouped_orders"]:
        for order_group in message["grouped_orders"]:
            body = {
                "bundle_request_id": message["bundle_request_id"],
                "order_list": order_group,
            }
            resp_bundles = handle_fallback_call(body)
            if resp_bundles:
                bundles.extend(resp_bundles)
    else:
        logger.warning(f"No grouped orders for bundle_request_id={in_message.engine_event_id}")

    # append "error bundles of 1"
    if message["error_orders"]:
        for err_order in message["error_orders"]:
            order_id = err_order["order_id"]
            logger.info(f"creating bundle of one: {order_id=}")
            bundles.extend([{"group_id": str(uuid4()), "orders": [order_id]}])

    if not bundles:
        logger.critical(f"{in_message.bundle_request_id} = NO BUNDLE SOLUTION - NO BUNDLES OF ONE")
        raise Exception(f"No bundles on req id {in_message.bundle_request_id}")

    fallback_solution = {"bundles": bundles}
    logger.info(f"{in_message.bundle_request_id} - optimized Bundles: {len(bundles)}")

    c = CollectFallback(
        engine_event_id=message["engine_event_id"],
        bundle_request_id=message["bundle_request_id"],
        fallback_id=str(uuid4()),
        fallback_finish=str(datetime.utcnow()),
        fallback_results=fallback_solution,
    )

    return [("collector", c)]
