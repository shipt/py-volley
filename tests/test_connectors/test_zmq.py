import os
from unittest.mock import MagicMock, patch

from volley.connectors.zmq import ZMQConsumer, ZMQProducer
from volley.data_models import QueueMessage


@patch("volley.connectors.zmq._socket")
def test_zmqconsumer(mocked_zsmq: MagicMock) -> None:
    msg = "test-message"
    mocked_zsmq.recv.return_value = msg
    consumer = ZMQConsumer(host="redis", queue_name="test", config={"port": 5555})
    consumed_msg = consumer.consume()
    assert isinstance(consumed_msg, QueueMessage)
    assert msg == consumed_msg.message

    # these dont do anything in the send-receive use-case
    consumer.on_fail("")
    consumer.on_success("")
    consumer.shutdown()


@patch("volley.connectors.zmq._socket")
@patch.dict(os.environ, {"ZMQ_PORT": "5555", "ZMQ_HOST": "test-host"}, clear=True)
def test_zmqconsumer_env_host(mocked_zsmq: MagicMock) -> None:  # pylint: disable=W0613
    """Verify ZMQ_HOST / ZMQ_PORT env vars are used when host / port is not
    specified in config.

    *IMPORTANT*: The `host` is never used. It's always 0.0.0.0.
    """

    msg = "test-message"
    mocked_zsmq.recv.return_value = msg
    # bug: The `host` attr is never used.
    # verify config values take priority over env vars
    consumer = ZMQConsumer(host="redis", queue_name="test", config={"host": "host", "port": "port"})
    assert consumer.config["host"] == "host"
    assert consumer.config["port"] == "port"

    # fallback to env vars
    consumer = ZMQConsumer(host="redis", queue_name="test")
    assert consumer.config["host"] == "test-host"
    assert consumer.config["port"] == "5555"

    consumed_msg = consumer.consume()
    assert isinstance(consumed_msg, QueueMessage)
    assert msg == consumed_msg.message
    consumer.shutdown()


@patch("volley.connectors.zmq._socket")
def test_zmqproducer(mocked_zsmq: MagicMock) -> None:  # pylint: disable=W0613
    msg = b"test-message"
    producer = ZMQProducer(host="redis", queue_name="test", config={"port": 5555})
    producer.produce(queue_name="test", message=msg)
    producer.shutdown()


@patch("volley.connectors.zmq._socket")
@patch.dict(os.environ, {"ZMQ_PORT": "5555", "ZMQ_HOST": "test-host"}, clear=True)
def test_zmqproducer_env_host(mocked_zsmq: MagicMock) -> None:  # pylint: disable=W0613
    """Verify ZMQ_HOST / ZMQ_PORT env vars are used when host / port is not
    specified in config.

    *IMPORTANT*: The `host` is never used. It's always 0.0.0.0.
    """

    msg = b"test-message"

    # The host set here *should* take priority over the env var, but it doesn't (bug).
    # The host is hardcoded to 0.0.0.0
    # verify config values take priority over env vars
    producer = ZMQProducer(host="redis", queue_name="test", config={"host": "host", "port": "port"})
    assert producer.config["host"] == "host"
    assert producer.config["port"] == "port"

    # fallback to env vars
    producer = ZMQProducer(host="redis", queue_name="test")
    assert producer.config["host"] == "test-host"
    assert producer.config["port"] == "5555"

    producer.produce(queue_name="test", message=msg)
    producer.shutdown()
