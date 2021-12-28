from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pytest import MonkeyPatch

from tests.conftest import KafkaMessage
from volley.connectors import ConfluentKafkaConsumer, ConfluentKafkaProducer
from volley.connectors.confluent import handle_creds
from volley.data_models import QueueMessage


def test_confluent_produce(mock_confluent_producer: ConfluentKafkaProducer) -> None:
    assert mock_confluent_producer.produce(queue_name="test-topic", message=b"{'foo':'bar'}")


def test_handle_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_BROKERS")
    with pytest.raises(KeyError):
        handle_creds(config={})


def test_handle_creds_config_dict(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_KEY", "get")
    monkeypatch.setenv("KAFKA_SECRET", "them")
    result = handle_creds(config={})
    assert result["sasl.username"] == "get"
    assert result["sasl.password"] == "them"
    assert result["security.protocol"] == "SASL_SSL"
    assert result["sasl.mechanism"] == "PLAIN"


def test_confluent_consumer_no_consumer_group() -> None:
    with pytest.raises(Exception):
        ConfluentKafkaConsumer(queue_name="input-topic")


def test_kafka_consumer_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    config = {"sasl.username": "test-user", "sasl.password": "test-password"}
    c = ConfluentKafkaConsumer(config=config, queue_name="input-topic")
    assert "sasl.username" in c.config
    assert "sasl.password" in c.config


def test_kafka_producer_creds() -> None:
    config = {"sasl.username": "test-user", "sasl.password": "test-password"}
    p = ConfluentKafkaProducer(config=config, queue_name="input-topic")
    assert "sasl.username" in p.config
    assert "sasl.password" in p.config


@patch("volley.connectors.confluent.KConsumer")
def test_consume(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=b'{"random": "message"}')
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert isinstance(q_message, QueueMessage)


@patch("volley.connectors.kafka.RUN_ONCE", True)
@patch("volley.connectors.confluent.KConsumer")
def test_consume_none(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: None
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.kafka.RUN_ONCE", True)
@patch("volley.connectors.confluent.KConsumer")
def test_consume_error(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(error=True)
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.confluent.KConsumer")
def test_consumer_group_init(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:  # pylint: disable=W0613
    with monkeypatch.context() as m:
        random_consumer_group = str(uuid4())
        m.setenv("KAFKA_CONSUMER_GROUP", random_consumer_group)
        m.setenv("KAFKA_BROKERS", "rando_kafka:9092")

        consumer = ConfluentKafkaConsumer(queue_name="input-topic")
        assert consumer.config["group.id"] == random_consumer_group
