import os
from typing import Optional
from unittest.mock import MagicMock, patch
from uuid import uuid4

from volley.config import APP_ENV
from volley.connectors import KafkaConsumer
from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage


class KafkaMessage:

    _error_msg = "MOCK ERORR"

    def __init__(self, error: bool = False) -> None:
        self.is_error = error

    def offset(self) -> int:
        return 123

    def value(self) -> bytes:
        return b'{"random": "message"}'

    def error(self) -> Optional[str]:
        if self.is_error:
            return self._error_msg
        return None


def test_kafka_producer(mock_kafka_producer: Producer, bundle_message: QueueMessage) -> None:

    assert mock_kafka_producer.produce(queue_name="test", message=bundle_message)


def test_kafka_consumer_success(mock_kafka_consumer: Consumer) -> None:
    bundle_message = mock_kafka_consumer.consume("test-q")
    assert isinstance(bundle_message, QueueMessage)


@patch("volley.connectors.kafka.KConsumer")
def test_consume(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage()
    b = KafkaConsumer(host="localhost", queue_name="input-queue")
    q_message = b.consume()
    assert isinstance(q_message, QueueMessage)


@patch("volley.connectors.kafka.RUN_ONCE", True)
@patch("volley.connectors.kafka.KConsumer")
def test_consume_error(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage(error=True)
    b = KafkaConsumer(host="localhost", queue_name="input-queue")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.kafka.KConsumer")
def test_consumer_group_init(mock_consumer: MagicMock) -> None:
    random_consumer_group = str(uuid4())
    env = {"KAFKA_CONSUMER_GROUP": random_consumer_group, "KAFKA_BROKERS": "rando_kafka:9092"}
    with patch.dict(os.environ, env, clear=True):
        consumer = KafkaConsumer(queue_name="input-queue")
        assert consumer.consumer_group == random_consumer_group

    del env["KAFKA_CONSUMER_GROUP"]
    with patch.dict(os.environ, env, clear=True):
        consumer = KafkaConsumer(queue_name="input-queue")
        assert APP_ENV in consumer.consumer_group
