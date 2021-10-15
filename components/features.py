import json
import os

import requests
from typing import Tuple

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
def main(message: BundleMessage) -> Tuple[BundleMessage, str]:
    message.message["features"] = {"feature": "random"}

    fp_url = fp_url_based_on_env()
    with open("./seed/fp_payload.json", "r") as file:
        data = json.load(file)
    response = requests.post(fp_url, data=json.dumps(data))
    logger.info(f"Flight Plan Calculator response: {response.json()}")
    
    message.message["flight_plan_estimate"] = response.json()

    next_queue = OUTPUT_QUEUES[0]
    return message, next_queue

