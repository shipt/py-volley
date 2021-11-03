import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import requests

from components.data_models import CollectOptimizer, OptimizerMessage
from core.logging import logger
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["collector"]
OPTIMIZER_URL = {
    "localhost": "https://ds-bundling.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "staging": "https://ds-bundling.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "production": "https://ds-bundling.ds.us-central1.shipt.com/v1/bundle/optimize",
}[os.getenv("APP_ENV", "localhost")]


def handle_optimizer_call(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    # convert schema
    for order in body["order_list"]:
        order["delv_latitude"] = order.pop("delivery_latitude")
        order["delv_longitude"] = order.pop("delivery_longitude")

    resp = requests.post(OPTIMIZER_URL, data=json.dumps(body, default=str))
    if resp.status_code == 200:
        bundles: List[Dict[str, Any]] = resp.json()["bundles"]
    else:
        logger.error(f"{OPTIMIZER_URL} -{resp.status_code=} - {resp.reason} - {body=}")
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

    for order_group in message["grouped_orders"]:
        body = {
            "bundle_request_id": message["bundle_request_id"],
            "order_list": order_group,
        }
        resp_bundles = handle_optimizer_call(body)
        if resp_bundles:
            bundles.extend(resp_bundles)

    # append "error bundles of 1"
    if message["error_orders"]:
        for err_order in message["error_orders"]:
            order_id = err_order["order_id"]
            logger.info(f"creating bundle of one: {order_id=}")
            bundles.extend([{"group_id": str(uuid4()), "orders": [order_id]}])

    opt_solution = {"bundles": bundles}
    logger.info(f"Optimized Bundles: {opt_solution}")

    c = CollectOptimizer(
        engine_event_id=in_message.engine_event_id,
        bundle_request_id=in_message.bundle_request_id,
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results=opt_solution,
    )

    return [("collector", c)]
