# example producer
# simulates some "external service" publishing data to a kafka topic that a Volley application consumes from
import time
from uuid import uuid4

from pyshipt_streams import KafkaProducer

from example.data_models import InputMessage
from volley.logging import logger
from volley.queues import available_queues


def main() -> None:
    queues = available_queues()
    input_topic = queues.queues["input-queue"].value
    logger.info(f"{input_topic=}")
    p = KafkaProducer()
    i = 0
    while True:
        data = InputMessage.schema()["examples"][0]
        uuid = str(uuid4())[:8]
        data["request_id"] = f"{uuid}-{i}"
        p.publish(input_topic, data, serialize=True)
        logger.info(f"{data=}")
        time.sleep(10)
        i += 1


if __name__ == "__main__":
    main()
