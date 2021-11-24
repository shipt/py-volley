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


env = Environment(
    brokers=os.environ["KAFKA_BROKERS"],
    input_topic=queues["input-queue"].value,
    output_topic=queues["output-queue"].value,
    dlq=queues["dead-letter-queue"].value,
)


@fixture
def environment() -> Environment:
    return env


def create_topics() -> None:
    # time for Kafka broker to init
    time.sleep(5)
    conf = {"bootstrap.servers": env.brokers}
    admin = confluent_kafka.admin.AdminClient(conf)
    topics = [confluent_kafka.admin.NewTopic(x, 1, 1) for x in [env.input_topic, env.output_topic, env.dlq]]
    admin.create_topics(topics)
    # TODO: add assertion for topics successfully created
    assert True


create_topics()
