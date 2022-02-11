# app_0.py
from typing import List, Tuple

from my_config import InputMessage, OutputMessage, queue_config

from volley import Engine

# the first node - reads from kafka and writes to redis
app_0 = Engine(
    app_name="app_0",
    input_queue="my-kafka-input",  # one input
    output_queues=["my-redis-output"],  # zero to many outputs
    queue_config=queue_config,
)


@app_0.stream_app
def kafka_to_redis(msg: InputMessage) -> List[Tuple[str, OutputMessage]]:
    print(f"Received {msg.json()}")
    max_val = max(msg.my_values)
    out = OutputMessage(the_max=max_val)
    print(out)
    return [("my-redis-output", out)]  # a list of one or many output targets and messages


if __name__ == "__main__":
    kafka_to_redis()
