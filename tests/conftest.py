import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch

import numpy as np
from pytest import fixture

from engine.data_models import BundleMessage, CollectorMessage
from engine.kafka import BundleConsumer as kafka_consumer
from engine.kafka import BundleProducer as kafka_producer
from engine.rsmq import BundleConsumer as rsmq_consumer
from engine.rsmq import BundleProducer as rsmq_producer

os.environ["INPUT_QUEUE"] = "input"
os.environ["OUTPUT_QUEUE"] = "output"
os.environ["REDIS_HOST"] = "redis"
os.environ["KAFKA_BROKERS"] = "kafka:9092"


@fixture
def collector_message() -> CollectorMessage:
    return CollectorMessage(
        engine_event_id="123",
        bundle_event_id="abc",
        store_id="store_a",
        timeout=str(datetime.now() + timedelta(minutes=10)),
        fallback_id="id_1",
        fallback_results={"bundles": ["bundle_a", "bundle_b"]},
        fallback_finish=str(datetime.now() + timedelta(minutes=2)),
        optimizer_i="id_2",
        optimizer_results={"bundles": ["bundle_a", "bundle_b"]},
        optimizer_finish=str(datetime.now() + timedelta(minutes=4)),
    )


@fixture
def bundle_message() -> BundleMessage:
    return BundleMessage(
        message_id="123",
        params={"timeout_seconds": 10},
        message={
            "engine_event_id": "123",
            "bundle_event_id": "abc",
            "store_id": "store_a",
            "orders": [1, 2, 3],
        },
    )


@fixture
def mock_rsmq_producer() -> rsmq_producer:
    with patch("engine.rsmq.RedisSMQ"):
        producer = rsmq_producer(
            host="redis",
            queue_name="test",
        )
        return producer


@fixture
def mock_rsmq_consumer() -> rsmq_consumer:
    msg = {"id": "abc123", "message": json.dumps({"kafka": "message"}).encode("utf-8")}
    with patch("engine.rsmq.RedisSMQ"):
        c = rsmq_consumer(
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
def mock_kafka_consumer() -> kafka_consumer:
    with patch("engine.kafka.KafkaConsumer"):
        c = kafka_consumer(host="kafka", queue_name="test")
        c.c.poll = MagicMock(return_value=KafkaMessage())
        return c


@fixture
def mock_kafka_producer() -> kafka_producer:
    with patch("engine.kafka.KafkaProducer"):
        producer = kafka_producer(host="kafka", queue_name="test")
        return producer


@fixture
def fp_response() -> Dict[str, Any]:
    with open("./tests/fixtures/fp_payload.json", "r") as file:
        data = json.load(file)
    yield data
