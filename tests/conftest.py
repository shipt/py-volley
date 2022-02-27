import json
import os
from random import randint
from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch

from pytest import MonkeyPatch, fixture

from volley.config import get_configs
from volley.connectors import (
    ConfluentKafkaConsumer,
    ConfluentKafkaProducer,
    RSMQConsumer,
    RSMQProducer,
)
from volley.data_models import GenericMessage, QueueMessage
from volley.engine import Engine
from volley.profiles import ConnectionType, Profile

os.environ["REDIS_HOST"] = "redis"
os.environ["KAFKA_BROKERS"] = "kafka:9092"
os.environ["KAFKA_CONSUMER_GROUP"] = "test-group"


@fixture
def bundle_message() -> QueueMessage:
    return QueueMessage(
        message_context="123",
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


@fixture
def mock_rsmq_consumer_id_bytes() -> RSMQConsumer:
    msg = {
        "id": bytes("xyz456", "utf-8"),
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


class KafkaMessage:
    _offset: int = randint(1, 200)
    _error_msg = "MOCK ERROR"
    _partition = 0

    def __init__(
        self,
        error: bool = False,
        msg: Optional[bytes] = None,
        topic: Optional[str] = None,
        partition: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> None:
        self._error = error
        self._value = msg
        self._topic = topic
        if partition:
            self._partition = partition
        if offset:
            self._offset = offset

    def error(self) -> bool:
        return self._error

    def offset(self) -> int:
        return self._offset

    def value(self) -> Optional[bytes]:
        return self._value

    def topic(self) -> Optional[str]:
        return self._topic

    def partition(self) -> int:
        return self._partition


@fixture
def mock_confluent_producer() -> ConfluentKafkaProducer:
    class MockConsumer:
        def on_success(*args: Any, **kwargs: Any) -> None:
            pass

        def on_fail(*args: Any, **kwargs: Any) -> None:
            pass

    mc = MockConsumer()

    with patch("volley.connectors.confluent.Producer"):
        producer = ConfluentKafkaProducer(queue_name="test")
        producer.init_callbacks(mc, thread=False)  # type: ignore
        return producer


@fixture
def mock_confluent_consumer() -> ConfluentKafkaConsumer:
    with patch("volley.connectors.confluent.Consumer"):
        consumer = ConfluentKafkaConsumer(queue_name="test")
        return consumer


@fixture
def none_producer_decorated(monkeypatch: MonkeyPatch) -> Generator[Callable[..., None], None, None]:
    monkeypatch.setattr("volley.connectors.confluent", "Producer", MagicMock())
    monkeypatch.setattr("volley.connectors.confluent", "Consumer", MagicMock())

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        metrics_port=None,
    )

    @eng.stream_app
    def func(*args: Any) -> bool:  # pylint: disable=W0613
        return True

    yield func


@fixture
def config_dict() -> Dict[str, Dict[str, Any]]:
    return {
        "input-topic": {
            "value": "localhost.kafka.input",
            "profile": "confluent",
            "data_model": "example.data_models.InputMessage",
        },
        "comp_1": {
            "value": "comp1",
            "profile": "rsmq",
            "data_model": GenericMessage,
        },
        "output-topic": {
            "value": "localhost.kafka.output",
            "profile": "confluent",
            "data_model": "volley.data_models.GenericMessage",
            "config": {"compression.type": "gzip"},
        },
        "dead-letter-queue": {
            "value": "localhost.kafka.dlq",
            "profile": "confluent-dlq",
        },
    }


@fixture
def confluent_consumer_profile() -> Profile:
    confluent_profile = get_configs()["profiles"]["confluent"]
    confluent_profile["connection_type"] = ConnectionType.CONSUMER
    return Profile(**confluent_profile)


@fixture
def confluent_producer_profile() -> Profile:
    confluent_profile = get_configs()["profiles"]["confluent"]
    confluent_profile["connection_type"] = ConnectionType.PRODUCER
    return Profile(**confluent_profile)


@fixture
def all_supported_producer_profiles() -> List[Profile]:
    all_cfg: Any = get_configs()["profiles"]
    for _, c in all_cfg.items():
        c["connection_type"] = ConnectionType.PRODUCER
    return [Profile(**c) for c in all_cfg.values()]


@fixture
def all_supported_consumer_profiles() -> List[Profile]:
    all_cfg: Any = get_configs()["profiles"]
    for _, c in all_cfg.items():
        c["connection_type"] = ConnectionType.CONSUMER
    return [Profile(**c) for c in all_cfg.values()]
