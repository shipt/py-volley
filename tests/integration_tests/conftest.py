import os
import time
from typing import Any, Dict, NamedTuple

import confluent_kafka.admin
from pytest import fixture

from volley.config import load_yaml
from volley.logging import logger
from volley.queues import Queue

queues: Dict[str, Any] = load_yaml("./example/volley_config.yml")["queues"]


class Environment(NamedTuple):
    brokers: str
    input_topic: str
    output_topic: str
    dlq: str


env = Environment(
    brokers=os.environ["KAFKA_BROKERS"],
    input_topic=queues["input-topic"]["value"],
    output_topic=queues["output-topic"]["value"],
    dlq=queues["dead-letter-queue"]["value"],
)


@fixture
def environment() -> Environment:
    return env


def pytest_configure() -> None:
    """creates topics and validates topic creation
    https://docs.pytest.org/en/latest/reference/reference.html#_pytest.hookspec.pytest_configure
    """
    all_topics = [env.input_topic, env.output_topic, env.dlq]
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
