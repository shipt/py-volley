import os
from datetime import datetime
from typing import List, Tuple
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


def opt_url_based_on_env() -> str:
    return OPTIMIZER_URL[os.getenv("APP_ENV", "localhost")]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: OptimizerMessage) -> List[Tuple[str, ComponentMessage]]:
    """handling calling the optimization service"""

    bundles = []
    for order_group in message.grouped_orders:
        body = {
            "bundle_request_id": message.bundle_request_id,
            "order_list": order_group,
        }
        resp = requests.post(OPTIMIZER_URL, json=body)
        if resp.status_code == 200:
            opt_response = resp.json()
            bundles.extend(opt_response["bundles"])
        else:
            logger.error(f"{OPTIMIZER_URL} -{resp.status_code=} - {resp.reason}")

    # append "error bundles of 1"
    if message.error_orders:
        for err_order in message.error_orders:
            order_id = err_order["order_id"]
            logger.info(f"creating bundle of one: {order_id=}")
            bundles.extend([{"group_id": str(uuid4()), "orders": [order_id]}])

    opt_solution = {"bundles": bundles}
    logger.info(f"Optimized Bundles: {opt_solution}")

    c = CollectOptimizer(
        engine_event_id=message.engine_event_id,
        bundle_request_id=message.bundle_request_id,
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results=opt_solution,
    )

    return [("collector", c)]
