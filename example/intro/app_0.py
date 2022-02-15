# app_0.py
import logging
from typing import List, Tuple

from my_config import InputMessage, OutputMessage, queue_config

from volley import Engine

logging.basicConfig(level=logging.INFO)


# the first node - reads from kafka and writes to redis
app_0 = Engine(
    app_name="app_0",
    input_queue="my-kafka-input",  # one input
    output_queues=["my-redis-output"],  # zero to many outputs
    queue_config=queue_config,
)


@app_0.stream_app
def kafka_to_redis(msg: InputMessage) -> List[Tuple[str, OutputMessage]]:
    logging.info(f"Received {msg.json()}")
    max_val = max(msg.my_values)
    out = OutputMessage(the_max=max_val)
    logging.info(out)
    return [("my-redis-output", out)]  # a list of output targets and messages


if __name__ == "__main__":
    kafka_to_redis()
