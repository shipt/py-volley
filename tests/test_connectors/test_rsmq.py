from unittest.mock import MagicMock, patch

from pytest import MonkeyPatch, raises

from volley.connectors import RSMQConsumer, RSMQProducer
from volley.connectors.rsmq import RSMQConfigError
from volley.data_models import QueueMessage


def test_rsmq_producer(mock_rsmq_producer: RSMQProducer, bundle_message: QueueMessage) -> None:
    assert mock_rsmq_producer.produce(queue_name="test", message=bundle_message.json().encode("utf-8"))


def test_rsmq_consumer(mock_rsmq_consumer: RSMQConsumer) -> None:

    assert mock_rsmq_consumer.consume(queue_name="test")


def test_rsmq_delete(mock_rsmq_consumer: RSMQConsumer) -> None:

    assert mock_rsmq_consumer.on_success(queue_name="test", message_context="abc123")


@patch("volley.connectors.rsmq.RedisSMQ")
def test_return_none(mocked_rsmq: MagicMock) -> None:
    mocked_rsmq.queue.receiveMessage.return_value.exceptions.return_value.execute = None
    consumer = RSMQConsumer(host="redis", queue_name="test")
    msg = consumer.consume(queue_name="test")
    assert msg is None

    consumer.on_fail()


@patch("volley.connectors.rsmq.RedisSMQ")
def test_init_config(mocked_rsmq: MagicMock, monkeypatch: MonkeyPatch) -> None:  # pylint: disable=W0613
    monkeypatch.setenv("REDIS_HOST", "env_redis")
    config = {
        "queue_name": "overwridden",
        "host": "override_redis",
        "options": {"decode_responses": False},
        "random": "overridden",
    }
    consumer = RSMQConsumer(queue_name="test", config=config.copy())
    producer = RSMQProducer(queue_name="test", config=config.copy())
    for k, v in config.items():
        # all overwrides must be present
        assert consumer.config[k] == v
        assert producer.config[k] == v

    del config["host"]
    config["options"] = {"someother": "configs"}
    consumer = RSMQConsumer(queue_name="test", config=config.copy())
    producer = RSMQProducer(queue_name="test", config=config.copy())
    assert consumer.config["host"] == "env_redis"
    assert producer.config["host"] == "env_redis"
    # and this is an important default
    assert consumer.config["options"]["decode_responses"] is False

    for k, v in config.items():
        # all overwrides must be present
        # host from env var
        assert consumer.config[k] == v
        assert producer.config[k] == v

    monkeypatch.delenv("REDIS_HOST")
    with raises(RSMQConfigError):
        # no host provided - should crash
        RSMQConsumer(queue_name="test", config=config.copy())
    with raises(RSMQConfigError):
        # no host provided - should crash
        RSMQProducer(queue_name="test", config=config.copy())
