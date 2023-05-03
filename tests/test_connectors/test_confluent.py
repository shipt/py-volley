import json
import logging
from random import randint
from typing import Any, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pytest import LogCaptureFixture, MonkeyPatch

from example.data_models import InputMessage, OutputMessage
from tests.conftest import KafkaMessage
from volley import Engine
from volley.connectors.confluent import (
    BatchJsonConfluentConsumer,
    ConfluentKafkaConsumer,
    ConfluentKafkaProducer,
    _handle_creds,
)
from volley.data_models import QueueMessage


def test_confluent_producer(mock_confluent_producer: ConfluentKafkaProducer) -> None:
    assert mock_confluent_producer.produce(
        queue_name="test-topic", message=b"{'foo':'bar'}", message_context="consumed_message_id"
    )
    mock_confluent_producer.shutdown()


def test_handle_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BROKERS", "brokers")
    monkeypatch.setenv("KAFKA_CONSUMER_BROKERS", "consumer_brokers")

    # Verify bootstrap.servers overrides all env vars
    creds = _handle_creds(config_dict={"bootstrap.servers": "default"}, is_consumer=True)
    assert creds["bootstrap.servers"] == "default"

    creds = _handle_creds(config_dict={}, is_consumer=False)
    assert creds["bootstrap.servers"] == "brokers"

    creds = _handle_creds(config_dict={}, is_consumer=True)
    assert creds["bootstrap.servers"] == "consumer_brokers"


def test_handle_creds_consumer_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BROKERS", "brokers")

    creds = _handle_creds(config_dict={}, is_consumer=False)
    assert creds["bootstrap.servers"] == "brokers"

    creds = _handle_creds(config_dict={}, is_consumer=True)
    assert creds["bootstrap.servers"] == "brokers"


def test_handle_consumer_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_BROKERS", raising=False)
    monkeypatch.delenv("KAFKA_CONSUMER_BROKERS", raising=False)

    with pytest.raises(ValueError):
        _handle_creds(config_dict={}, is_consumer=True)
    with pytest.raises(ValueError):
        _handle_creds(config_dict={}, is_consumer=False)

    # Setting the consumers variable - consumer config will work, producer will not
    monkeypatch.setenv("KAFKA_CONSUMER_BROKERS", "consumer_brokers")
    creds = _handle_creds(config_dict={}, is_consumer=True)
    assert creds["bootstrap.servers"] == "consumer_brokers"

    with pytest.raises(ValueError):
        _handle_creds(config_dict={}, is_consumer=False)


def test_handle_creds_config_dict(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_KEY", "get")
    monkeypatch.setenv("KAFKA_SECRET", "them")
    result = _handle_creds(config_dict={}, is_consumer=True)
    assert result["sasl.username"] == "get"
    assert result["sasl.password"] == "them"
    assert result["security.protocol"] == "SASL_SSL"
    assert result["sasl.mechanism"] == "PLAIN"


@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_confluent_consumer_no_consumer_group(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("KAFKA_CONSUMER_GROUP")
    with pytest.raises(Exception):
        ConfluentKafkaConsumer(queue_name="input-topic")


@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_kafka_consumer_creds(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    config = {"sasl.username": "test-user", "sasl.password": "test-password"}
    c = ConfluentKafkaConsumer(config=config, queue_name="input-topic")
    assert "sasl.username" in c.config
    assert "sasl.password" in c.config


@patch("volley.connectors.confluent.Producer", MagicMock())
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
    b.on_fail(kmsg)


@patch("volley.connectors.confluent.Consumer")
def test_consume_none(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")
    mock_consumer.return_value.poll = lambda x: None
    b = ConfluentKafkaConsumer(host="localhost", queue_name="input-topic")
    q_message = b.consume()
    assert q_message is None


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


@patch("volley.connectors.confluent.Producer", MagicMock())
def test_callback(mock_confluent_producer: ConfluentKafkaProducer, caplog: LogCaptureFixture) -> None:
    mock_confluent_producer.on_fail = MagicMock()
    mock_confluent_producer.on_success = MagicMock()
    caplog.set_level(logging.DEBUG)

    m = KafkaMessage()
    expected_log_error = "my-logged-error"
    mock_confluent_producer.acked(err=expected_log_error, msg=m, consumer_context="consumed_message_id")
    assert "failed delivery" in caplog.messages[0].lower()
    m = KafkaMessage(topic="test-topic")
    mock_confluent_producer.acked(err=None, msg=m, consumer_context="consumed_message_id")
    assert "test-topic" in caplog.messages[1]
    assert "successful delivery" in caplog.messages[1].lower()
    mock_confluent_producer.shutdown()


@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_consumer_init_configs() -> None:
    rand_interval = randint(0, 100)
    config = {"poll_interval": rand_interval, "auto.offset.reset": "latest"}
    con = ConfluentKafkaConsumer(queue_name="test", config=config)
    assert con.poll_interval == rand_interval
    assert con.config["auto.offset.reset"] == "latest"


@patch("volley.connectors.confluent.Producer", MagicMock())
def test_producer_init_configs() -> None:
    config = {"compression.type": "snappy", "poll_thread_timeout": 1}
    p = ConfluentKafkaProducer(queue_name="test", config=config)
    assert p.config["compression.type"] == "snappy"
    p.shutdown()


@pytest.mark.parametrize(
    "queue",
    [("topic0"), ("topic0,topic1,topic2")],
)
@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_callback_consumer(queue: str) -> None:
    topics = queue.split(",")
    ackc = ConfluentKafkaConsumer(queue_name=queue)

    # first commit
    for topic in topics:
        m = KafkaMessage(topic=topic, partition=24, offset=42)
        ackc.on_success(m)
        assert ackc.last_offset[topic][24] == 42

    # commit a higher offset, same partition
    for topic in topics:
        m = KafkaMessage(topic=topic, partition=24, offset=43)
        ackc.on_success(m)
        assert ackc.last_offset[topic][24] == 43

    # commit a lower offset, same partition
    # should not change the last commit
    for topic in topics:
        m = KafkaMessage(topic=topic, partition=24, offset=1)
        ackc.on_success(m)
        assert ackc.last_offset[topic][24] == 43

    # commit to different partition
    for topic in topics:
        m = KafkaMessage(topic=topic, partition=1, offset=100)
        ackc.on_success(m)
        assert ackc.last_offset[topic][1] == 100
        assert ackc.last_offset[topic][24] == 43

    # repeatedly commit same data
    for topic in topics:
        m = KafkaMessage(topic=topic, partition=1, offset=100)
        for _ in range(10):
            ackc.on_success(m)
        assert ackc.last_offset[topic][1] == 100
        assert ackc.last_offset[topic][24] == 43


@patch("volley.connectors.confluent.os", MagicMock())
@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_downstream_failure(caplog: LogCaptureFixture) -> None:
    """validate a downstream failure triggers the expected connector's shutdown procedure"""
    config = {"stop_on_failure": True}
    p = ConfluentKafkaConsumer(queue_name="test", config=config)

    with caplog.at_level(logging.ERROR):
        p.on_fail(message_context=KafkaMessage())
    assert "stopping application" in caplog.text.lower()

    config = {"stop_on_failure": False}
    p = ConfluentKafkaConsumer(queue_name="test", config=config)

    with caplog.at_level(logging.WARNING):
        p.on_fail(message_context=KafkaMessage())
    assert "critical" in caplog.text.lower()


@patch("volley.connectors.rsmq.RSMQProducer")
@patch("volley.connectors.confluent.Consumer")
def test_downstream_failure_shutdown(
    mock_consumer: MagicMock, mock_producer: MagicMock, caplog: LogCaptureFixture
) -> None:
    """Validate a downstream failure triggers all the expected graceful shutdown procedures"""
    eng = Engine(
        input_queue="input-topic",
        output_queues=["redis_queue"],
        yaml_config_path="./example/volley_config.yml",
        metrics_port=None,
    )

    input_msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=input_msg)

    # for simplicity, make it a synchronous producer
    mock_producer.return_value.callback_delivery = False
    # mock the failure to produce
    mock_producer.return_value.produce = lambda *args, **kwargs: False

    # dummy output object to try to produce
    output_msg = OutputMessage.parse_obj(OutputMessage.schema()["examples"][0])

    @eng.stream_app
    def func(msg: Any) -> List[Tuple[str, OutputMessage]]:
        print(msg.json())
        return [("redis_queue", output_msg)]

    # function should run then exit
    with caplog.at_level(logging.INFO):
        func()

    # make sure volley's graceful killer is set to shutdown
    assert eng.killer.kill_now is True
    assert "downstream failure" in caplog.text.lower()
    assert "shutdown volley complete" in caplog.text.lower()


@patch("volley.connectors.confluent.Consumer")
def test_batch_consumer_success(monkeypatch: MonkeyPatch) -> None:
    """validate success modes on batch consumer"""
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")

    batch_size = BatchJsonConfluentConsumer.batch_size

    topic = "test-topic"
    partition = 0
    from uuid import uuid4

    messages: List[KafkaMessage] = []
    for i in range(batch_size):
        messages.append(
            KafkaMessage(
                msg=json.dumps({"random": str(uuid4())}).encode("utf-8"), partition=partition, offset=i, topic=topic
            )
        )
    b = BatchJsonConfluentConsumer(host="localhost", queue_name=topic)
    b.c.consume = MagicMock(return_value=messages)
    q_message = b.consume()

    assert isinstance(q_message, QueueMessage)

    mocked_messages = [json.loads(m.value()) for m in messages]  # type: ignore
    consumed_messages = json.loads(q_message.message)
    assert mocked_messages == consumed_messages

    b.on_success(q_message.message_context)
    # offset must be the highest offset in the mocked messages
    assert b.last_offset[topic][partition] == i


@patch("volley.connectors.confluent.Consumer")
def test_batch_consumer_fail(monkeypatch: MonkeyPatch) -> None:
    """validate error modes on batch consumer"""
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")

    topic = "test-topic"
    b = BatchJsonConfluentConsumer(host="localhost", queue_name=topic)
    # mock Consumer.consume returning empty list (no messages)
    b.c.consume = MagicMock(return_value=[])
    q_message = b.consume()
    assert q_message is None

    # an error message also returns None
    err_msg = [KafkaMessage(error=True)]
    b.c.consume = MagicMock(return_value=err_msg)
    q_message = b.consume()
    assert q_message is None


@patch("volley.connectors.confluent.Consumer")
def test_batch_consumer_config(monkeypatch: MonkeyPatch) -> None:
    """validate error modes on batch consumer"""
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "test-group")

    topic = "test-topic"
    batch_size = randint(1, 20)
    batch_time = randint(1, 5)
    cfg = {"batch_size": batch_size, "batch_time_seconds": batch_time}
    b = BatchJsonConfluentConsumer(host="localhost", queue_name=topic, config=cfg)
    assert b.batch_size == batch_size
    assert b.batch_time_seconds == batch_time
