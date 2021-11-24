import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Generator
from unittest.mock import MagicMock, patch

import numpy as np
from pytest import MonkeyPatch, fixture

from volley.connectors import KafkaConsumer, KafkaProducer, RSMQConsumer, RSMQProducer
from volley.data_models import QueueMessage
from volley.engine import Engine

os.environ["INPUT_QUEUE"] = "input"
os.environ["OUTPUT_QUEUE"] = "output"
os.environ["REDIS_HOST"] = "redis"
os.environ["KAFKA_BROKERS"] = "kafka:29092"


@fixture
def bundle_message() -> QueueMessage:
    return QueueMessage(
        message_id="123",
        message={
            "request_id": "123",
            "orders": ["1", "2", "3"],
        },
    )


@fixture
def mock_rsmq_producer() -> RSMQProducer:
    with patch("volley.connectors.rsmq.RedisSMQ"):
        producer = RSMQProducer(
            host="redis",
            queue_name="test",
        )
        return producer


@fixture
def mock_rsmq_consumer() -> RSMQConsumer:
    msg = {
        "id": "abc123",
        "message": json.dumps({"kafka": "message"}).encode("utf-8"),
    }
    with patch("volley.connectors.rsmq.RedisSMQ"):
        c = RSMQConsumer(
            host="redis",
            queue_name="test",
        )
        execute = MagicMock(return_value=msg)
        c.queue.receiveMessage.return_value.exceptions.return_value.execute = (
            execute  # MagicMock(return_value=exceptions)
        )
        return c


@dataclass
class KafkaMessage:

    _error: bool = False
    _offset: int = np.random.randint(1, 200)
    _value: bytes = json.dumps({"kafka": "message"}).encode("utf-8")

    def error(self) -> bool:
        return self._error

    def offset(self) -> int:
        return self._offset

    def value(self) -> bytes:
        return self._value


@fixture()
def mock_kafka_consumer() -> KafkaConsumer:
    with patch("volley.connectors.kafka.KConsumer"):
        c = KafkaConsumer(host="kafka", queue_name="test")
        c.c.poll = MagicMock(return_value=KafkaMessage())
        return c


@fixture
def mock_kafka_producer() -> KafkaProducer:
    with patch("volley.connectors.kafka.KProducer"):
        producer = KafkaProducer(host="kafka", queue_name="test")
        return producer


@fixture
def none_producer_decorated(monkeypatch: MonkeyPatch) -> Generator[Callable[..., None], None, None]:
    eng = Engine(
        input_queue="input-topic", output_queues=["output-topic"], yaml_config_path="./example/volley_config.yml"
    )

    monkeypatch.setattr("volley.engine", "METRICS_ENABLED", False)
    monkeypatch.setattr("volley.connectors.kafka", "KProducer", MagicMock())
    monkeypatch.setattr("volley.connectors.kafka", "KConsumer", MagicMock())

    @eng.stream_app
    def func(*args: Any) -> None:
        return None

    yield func


@fixture
def config_dict() -> dict[str, dict[str, str]]:
    return {
        "input-topic": {
            "value": "localhost.kafka.input",
            "type": "kafka",
            "schema": "example.data_models.InputMessage",
        },
        "comp_1": {
            "value": "comp1",
            "type": "rsmq",
            "schema": "dict",
        },
        "output-topic": {
            "value": "localhost.kafka.output",
            "type": "kafka",
            "schema": "volley.data_models.ComponentMessage",
        },
        "dead-letter-queue": {
            "value": "localhost.kafka.dlq",
            "type": "kafka",
            "schema": "volley.data_models.ComponentMessage",
        },
    }
