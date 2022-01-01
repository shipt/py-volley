# example producer
# simulates some "external service" publishing data to a kafka topic that a Volley application consumes from
import json
import os
import time
from uuid import uuid4

from confluent_kafka import Producer

from example.data_models import InputMessage
from volley.config import load_yaml
from volley.logging import logger


def main() -> None:
    """produces example data to a topic. mimics a data producer external to Volley"""
    queues = load_yaml("./example/volley_config.yml")["queues"]
    input_topic = queues["input-topic"]["value"]
    logger.info(f"{input_topic=}")
    p = Producer({"bootstrap.servers": os.environ["KAFKA_BROKERS"]})
    i = 0
    while True:
        uuid = str(uuid4())[:8]
        data = InputMessage(
            list_of_values = [1, 2, 3, 4.5],
            request_id=f"{uuid}-{i}"
        )
        p.produce(input_topic, data.json())
        logger.info(f"{data=}")
        time.sleep(2)
        i += 1


if __name__ == "__main__":
    main()
