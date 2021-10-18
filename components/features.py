import json
import os
from typing import List, Tuple
from uuid import uuid4

import requests

from core.logging import logger
from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = "input-queue"
OUTPUT_QUEUES = ["triage"]
FLIGHT_PLAN_URL = {
    "localhost": "https://flight-plan-calculator.us-east-1.staging.shipt.com/calculate",
    "staging": "https://flight-plan-calculator.us-east-1.staging.shipt.com/calculate",
    "production": "https://flight-plan-calculator.us-east-1.shipt.com/calculate",
}


def fp_url_based_on_env() -> str:
    return FLIGHT_PLAN_URL[os.getenv("APP_ENV", "localhost")]


@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: BundleMessage) -> List[Tuple[str, BundleMessage]]:
    fp_responses = [
        requests.post(fp_url_based_on_env(), data=json.dumps(order))
        for order in message.message.get("orders")
    ]
    logger.info(
        f"Flight Plan Calculator estimates: {[response.json() for response in fp_responses]}"
    )

    message.message["features"] = {"feature": "random"}
    message.message["engine_event_id"] = str(uuid4())
    message.message["flight_plan_estimates"] = [
        response.json() for response in fp_responses
    ]

    return [("triage", message)]
