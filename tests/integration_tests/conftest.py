import os
import time
from typing import Any, Dict, NamedTuple

import confluent_kafka.admin
import pytest
from confluent_kafka import Consumer, Producer
from pytest import fixture

from volley.config import load_yaml
from volley.logging import logger

queues: Dict[str, Any] = load_yaml("./example/volley_config.yml")["queues"]


class Environment(NamedTuple):
    brokers: str
    input_topic: str
    output_topic: str
    dlq: str
    test_topic: str
    consumer_group: str
    kafka_to_kafka_input: str
    kafka_to_kafka_output: str
    redis_to_kafka_output: str
    redis_host: str


env = Environment(
    brokers=os.environ["KAFKA_BROKERS"],
    input_topic=queues["input-topic"]["value"],
    output_topic=queues["output-topic"]["value"],
    dlq=queues["dead-letter-queue"]["value"],
    test_topic="some-test-topic",
    consumer_group="int-test-group",
    kafka_to_kafka_input="localhost.kafka.kafka.input",
    kafka_to_kafka_output="localhost.kafka.kafka.output",
    redis_to_kafka_output="localhost.redis.kafka.output",
    redis_host=os.environ["REDIS_HOST"],
)


@fixture
def broker_config() -> dict[str, str]:
    return {"bootstrap.servers": env.brokers, "group.id": env.consumer_group, "auto.offset.reset": "earliest"}


@fixture
def environment() -> Environment:
    return env


@fixture
def int_test_producer() -> Producer:
    conf = {"bootstrap.servers": env.brokers}
    return Producer(conf)


@fixture
def int_test_consumer() -> Consumer:
    conf = {"bootstrap.servers": env.brokers, "group.id": env.consumer_group, "auto.offset.reset": "earliest"}
    return Consumer(conf)


@pytest.mark.integration
def pytest_configure() -> None:
    """creates topics and validates topic creation
    https://docs.pytest.org/en/latest/reference/reference.html#_pytest.hookspec.pytest_configure
    """
    all_topics = [
        env.input_topic,
        env.output_topic,
        env.dlq,
        env.test_topic,
        env.kafka_to_kafka_input,
        env.kafka_to_kafka_output,
        env.redis_to_kafka_output,
    ]
    conf = {"bootstrap.servers": env.brokers}
    topics = [confluent_kafka.admin.NewTopic(x, 1, 1) for x in all_topics]
    for _ in range(30):
        do_retry = 0
        broker_topics = []
        try:
            admin = confluent_kafka.admin.AdminClient(conf)
            admin.create_topics(topics)
            broker_topics = admin.list_topics(timeout=1).topics
        except Exception:
            logger.exception("list topic failed. waiting...")
        for t in all_topics:
            if t not in broker_topics:
                do_retry += 1
        if do_retry == 0:
            logger.info(f"{all_topics} present and accounted for")
            break
        time.sleep(2)

    assert do_retry == 0
