import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import numpy as np
from pytest import fixture

from components.data_models import (
    CollectFallback,
    CollectOptimizer,
    CollectTriage,
    InputMessage,
    PublisherMessage,
)
from engine.connectors.kafka import BundleConsumer as KafkaConsumer
from engine.connectors.kafka import BundleProducer as KafkaProducer
from engine.connectors.rsmq import BundleConsumer as RsmqConsumer
from engine.connectors.rsmq import BundleProducer as RsmqProducer
from engine.data_models import QueueMessage

os.environ["INPUT_QUEUE"] = "input"
os.environ["OUTPUT_QUEUE"] = "output"
os.environ["REDIS_HOST"] = "redis"
os.environ["KAFKA_BROKERS"] = "kafka:9092"


@fixture
def input_message() -> InputMessage:
    d = InputMessage.schema()["examples"][0]
    return InputMessage(**d)


@fixture
def collector_triage_message() -> CollectTriage:
    return CollectTriage(
        engine_event_id="123",
        bundle_request_id="abc",
        timeout=str(datetime.utcnow() + timedelta(minutes=10)),
    )


@fixture
def collector_fallback_message() -> CollectFallback:
    return CollectFallback(
        engine_event_id="123",
        bundle_request_id="abc",
        fallback_id="id_1",
        fallback_results={"bundles": [{"group_id": "group_a", "orders": ["bundle_a", "bundle_b"]}]},
        fallback_finish=str(datetime.utcnow() + timedelta(minutes=2)),
    )


@fixture
def collector_optimizer_message() -> CollectOptimizer:
    return CollectOptimizer(
        engine_event_id="123",
        bundle_request_id="abc",
        optimizer_id="id_2",
        optimizer_results={"bundles": [{"group_id": "group_a", "orders": ["bundle_a", "bundle_b"]}]},
        optimizer_finish=str(datetime.utcnow() + timedelta(minutes=4)),
    )


@fixture
def publisher_complete_message() -> PublisherMessage:
    return PublisherMessage.parse_obj(PublisherMessage.schema()["examples"][0])


@fixture
def bundle_message() -> QueueMessage:
    return QueueMessage(
        message_id="123",
        message={
            "engine_event_id": "123",
            "bundle_request_id": "abc",
            "orders": ["1", "2", "3"],
        },
    )


@fixture
def mock_rsmq_producer() -> RsmqProducer:
    with patch("engine.connectors.rsmq.RedisSMQ"):
        producer = RsmqProducer(
            host="redis",
            queue_name="test",
        )
        return producer


@fixture
def mock_rsmq_consumer() -> RsmqConsumer:
    msg = {
        "id": "abc123",
        "message": json.dumps({"kafka": "message"}).encode("utf-8"),
    }
    with patch("engine.connectors.rsmq.RedisSMQ"):
        c = RsmqConsumer(
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
    with patch("engine.connectors.kafka.KafkaConsumer"):
        c = KafkaConsumer(host="kafka", queue_name="test")
        c.c.poll = MagicMock(return_value=KafkaMessage())
        return c


@fixture
def mock_kafka_producer() -> KafkaProducer:
    with patch("engine.connectors.kafka.KafkaProducer"):
        producer = KafkaProducer(host="kafka", queue_name="test")
        return producer


@fixture
def fp_calculator_response() -> Any:
    with open("./tests/fixtures/fp_calculator_response.json", "r") as file:
        data = json.load(file)
    return data


@fixture
def fp_service_response() -> Dict[str, Any]:
    with open("./tests/fixtures/fp_service_response.json", "r") as f:
        data: Dict[str, Any] = json.load(f)
    return data
