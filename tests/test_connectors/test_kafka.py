import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pytest import MonkeyPatch, raises

from tests.conftest import KafkaMessage
from volley.config import APP_ENV
from volley.connectors import KafkaConsumer, KafkaProducer
from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage


def test_kafka_producer(mock_kafka_producer: Producer, bundle_message: QueueMessage) -> None:

    assert mock_kafka_producer.produce(queue_name="test", message=bundle_message.json().encode("utf-8"))


def test_kafka_consumer_fail(mock_kafka_consumer: Consumer) -> None:
    assert mock_kafka_consumer.on_fail() is None


def test_kafka_consumer_success(mock_kafka_consumer: Consumer) -> None:
    bundle_message = mock_kafka_consumer.consume("test-q")
    assert isinstance(bundle_message, QueueMessage)


@patch("volley.connectors.kafka.KConsumer")
def test_consume(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=b'{"random": "message"}')
    b = KafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert isinstance(q_message, QueueMessage)


@patch("volley.connectors.kafka.RUN_ONCE", True)
@patch("volley.connectors.kafka.KConsumer")
def test_consume_none(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: None
    b = KafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.kafka.RUN_ONCE", True)
@patch("volley.connectors.kafka.KConsumer")
def test_consume_error(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage(error=True)
    b = KafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.kafka.KConsumer")
def test_consumer_group_init(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:  # pylint: disable=W0613
    with monkeypatch.context() as m:
        random_consumer_group = str(uuid4())
        m.setenv("KAFKA_CONSUMER_GROUP", random_consumer_group)
        m.setenv("KAFKA_BROKERS", "rando_kafka:9092")

        consumer = KafkaConsumer(queue_name="input-topic")
        assert consumer.config["group.id"] == random_consumer_group

        m.delenv("KAFKA_CONSUMER_GROUP")
        consumer = KafkaConsumer(queue_name="input-topic")
        assert APP_ENV in consumer.config["group.id"]

        m.setattr(sys, "argv", "")
        with raises(Exception):
            # fallback to parsing sys.argv fails if its not provided
            KafkaConsumer(queue_name="input-topic")
