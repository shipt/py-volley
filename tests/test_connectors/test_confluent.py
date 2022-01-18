from random import randint
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pytest import LogCaptureFixture, MonkeyPatch

from tests.conftest import KafkaMessage
from volley.connectors import ConfluentKafkaConsumer, ConfluentKafkaProducer
from volley.connectors.confluent import handle_creds
from volley.data_models import QueueMessage


def test_confluent_producer(mock_confluent_producer: ConfluentKafkaProducer) -> None:
    assert mock_confluent_producer.produce(queue_name="test-topic", message=b"{'foo':'bar'}")
    mock_confluent_producer.shutdown()


def test_handle_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_BROKERS")
    with pytest.raises(KeyError):
        handle_creds(config_dict={})


def test_handle_creds_config_dict(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_KEY", "get")
    monkeypatch.setenv("KAFKA_SECRET", "them")
    result = handle_creds(config_dict={})
    assert result["sasl.username"] == "get"
    assert result["sasl.password"] == "them"
    assert result["security.protocol"] == "SASL_SSL"
    assert result["sasl.mechanism"] == "PLAIN"


def test_confluent_consumer_no_consumer_group(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_CONSUMER_GROUP")
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


@patch("volley.connectors.confluent.Consumer")
def test_consumer(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    kmsg = KafkaMessage(msg=b'{"random": "message"}')
    mock_consumer.return_value.poll = lambda x: kmsg
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert isinstance(q_message, QueueMessage)
    b.on_fail("test_q", kmsg)


@patch("volley.connectors.confluent.RUN_ONCE", True)
@patch("volley.connectors.confluent.Consumer")
def test_consume_none(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: None
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.confluent.RUN_ONCE", True)
@patch("volley.connectors.confluent.Consumer")
def test_consume_error(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(error=True)
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.confluent.Consumer")
def test_consumer_group_init(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:  # pylint: disable=W0613
    with monkeypatch.context() as m:
        random_consumer_group = str(uuid4())
        m.setenv("KAFKA_CONSUMER_GROUP", random_consumer_group)
        m.setenv("KAFKA_BROKERS", "rando_kafka:9092")

        consumer = ConfluentKafkaConsumer(queue_name="input-topic")
        assert consumer.config["group.id"] == random_consumer_group


def test_callback(mock_confluent_producer: ConfluentKafkaProducer, caplog: LogCaptureFixture) -> None:
    m = KafkaMessage()
    mock_confluent_producer.acked(err="error", msg=m)
    assert "Failed to deliver" in caplog.messages[0]
    m = KafkaMessage(topic="test-topic")
    mock_confluent_producer.acked(err=None, msg=m)
    assert "test-topic" in caplog.messages[1]


def test_consumer_init_configs() -> None:
    rand_interval = randint(0, 100)
    config = {"poll_interval": rand_interval, "auto.offset.reset": "latest"}
    con = ConfluentKafkaConsumer(queue_name="test", config=config)
    assert con.poll_interval == rand_interval
    assert con.config["auto.offset.reset"] == "latest"


def test_producer_init_configs() -> None:
    config = {"compression.type": "snappy"}
    p = ConfluentKafkaProducer(queue_name="test", config=config)
    assert p.config["compression.type"] == "snappy"
