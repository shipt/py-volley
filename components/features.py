import os
from typing import List, Tuple
from uuid import uuid4

import requests

from core.logging import logger
from engine.data_models import ComponentMessage
from engine.engine import bundle_engine

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]
FLIGHT_PLAN_URL = {
    "localhost": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "staging": "https://flight-plan-service.us-east-1.staging.shipt.com/v1/orders",
    "production": "https://flight-plan-service.us-east-1.shipt.com/v1/orders",
}


def fp_url_based_on_env() -> str:
    return FLIGHT_PLAN_URL[os.getenv("APP_ENV", "localhost")]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(in_message: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
    message = in_message.dict()
    fp_responses = [requests.get(f"{fp_url_based_on_env()}/{order}") for order in message.get("orders")]  # type: ignore
    logger.info(f"Flight Plan Calculator estimates: {[response.json() for response in fp_responses]}")

    message["bundle_event_id"] = message["bundle_request_id"]
    message["engine_event_id"] = str(uuid4())
    message["enriched_orders"] = [
        {
            "order_id": response.json().get("order_id"),
            "shop_time": response.json().get("before_claim").get("shop").get("minutes")
        } for response in fp_responses
    ]
    output_message = ComponentMessage(**message)
    return [("triage", output_message)]
