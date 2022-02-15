# app_1.py
import logging
from typing import List, Tuple, Union

from my_config import InputMessage, OutputMessage, queue_config

from volley import Engine

logging.basicConfig(level=logging.INFO)


# the second node
app_1 = Engine(
    app_name="app_1",
    input_queue="my-redis-output",
    output_queues=["my-kafka-input"],
    queue_config=queue_config,
    metrics_port=None,
)


@app_1.stream_app
def redis_to_kafka(msg: OutputMessage) -> Union[bool, List[Tuple[str, InputMessage]]]:
    logging.info(f"The maximum: {msg.the_max}")
    if msg.the_max > 10:
        logging.info("That's it, we are done!")
        return True
    else:
        out = InputMessage(my_values=[msg.the_max, msg.the_max + 1, msg.the_max + 2])
        return [("my-kafka-input", out)]  # a list of one or many output targets and messages


if __name__ == "__main__":
    redis_to_kafka()
