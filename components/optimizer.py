import os
import requests
import json
import time
import pandas as pd
import jsonschema as js
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from core.logging import logger
from components.data_models import CollectOptimizer, CollectorMessage
from engine.engine import bundle_engine
from engine.data_models import ComponentMessage
# from components.data_models import Bundle


INPUT_QUEUE = "optimizer"
OUTPUT_QUEUES = ["collector"]
OPTIMIZER_URL = {
    "localhost": "https://ds-bundling.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "staging": "https://ds-bundling.ds.us-central1.staging.shipt.com/v1/bundle/optimize",
    "production": "https://ds-bundling.ds.us-central1.shipt.com/v1/bundle/optimize"
}[os.getenv("APP_ENV", "localhost")]
# "localhost": "http://0.0.0.0:3000/v1/bundle/optimize",
# "staging": "http://0.0.0.0:3000/v1/bundle/optimize",
# "production": "http://0.0.0.0:3000/v1/bundle/optimize"

def opt_url_based_on_env() -> str:
    return OPTIMIZER_URL[os.getenv("APP_ENV", "localhost")]

bundle_schema = {"bundles": [{
                                "order_id": 0,
                                "bundle_id": "string"
                            }]
                }
# class Bundle(BaseModel):
#     group_id: str
#     orders: List[int]

@bundle_engine(input_queue=INPUT_QUEUE, output_queues=OUTPUT_QUEUES)
def main(message: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
    print('OPTIMIZER INPUT MESSAGE: ', message)

    # from ex_opt_data import ex_opt_data
    # data = ex_opt_data()
    # request_url = 'http://0.0.0.0:3000/v1/bundle/optimize'
    # request_url = 'https://ds-bundling.ds.us-central1.staging.shipt.com/v1/bundle/optimize'
    # resp = requests.post(opt_url_based_on_env(), data=json.dumps(data))

    ''' GROUP ORDERS BY TIME WINDOW & COLLECT REQUESTS '''
    order_lst = message.message.get("order_list")
    orders = pd.concat(order_lst)
    orders['TW_HR'] = pd.to_datetime(orders['delivery_start_time']).dt.hour
    orders = orders.sort_values('TW_HR')
    bundles = []
    for hour in orders['TW_HR']:
        # grouped_orders.append(orders[orders['TW_HR'] == hours])
        orders = orders[orders['TW_HR'] == hour]
        resp = requests.post(opt_url_based_on_env(), data=json.dumps(orders))
        if js.validate(json.loads(resp), bundle_schema):
            if (resp.status_code == 200):
                print('OPTIMIZER RESPONSE: ', resp.json())
                bundles.append(resp)
        elif (resp.status_code == 404):
            print('Error retrieving response from bundling optimizer.')
            print(resp.json())
        elif (resp.status_code == 422):
            print('Bundling optimizer validation error.')
            print(resp.json())

    opt_solution = {
        "bundles": [response.json() for response in bundles]
    }
    logger.info(
        f"Optimized Bundles: {[response.json() for response in bundles]}"
    )

    c = CollectOptimizer(
        engine_event_id=message.engine_event_id,
        bundle_request_id=message.bundle_request_id,
        optimizer_id=str(uuid4()),
        optimizer_finish=str(datetime.now()),
        optimizer_results=opt_solution,
    )

    return [("collector", c)]
