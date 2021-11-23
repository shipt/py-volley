import os
import time
from typing import Dict, NamedTuple

import confluent_kafka.admin
from pytest import fixture

from volley.queues import Queue, available_queues

queues: Dict[str, Queue] = available_queues("./example/volley_config.yml")


class Environment(NamedTuple):
    brokers: str
    input_topic: str
    output_topic: str
    dlq: str


@fixture
def environment() -> Environment:
    return Environment(
        brokers=os.environ["KAFKA_BROKERS"],
        input_topic=queues["input-queue"].value,
        output_topic=queues["output-queue"].value,
        dlq=queues["dead-letter-queue"].value,
    )


def test_create_topics(environment: Environment) -> None:
    # time for Kafka broker to init
    time.sleep(5)
    conf = {"bootstrap.servers": environment.brokers}
    admin = confluent_kafka.admin.AdminClient(conf)
    topics = [
        confluent_kafka.admin.NewTopic(x, 1, 1)
        for x in [environment.input_topic, environment.output_topic, environment.dlq]
    ]
    admin.create_topics(topics)
    # TODO: add assertion for topics successfully created
    assert True
