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
    """Verify ZMQ_HOST takes priority over ZMQ_PORT

    Setting "host" will allow us to set the host, but the host will never be
    used (bug).

    Verify that the internal config class accepts host / port env vars
    appropriately.

    """

    msg = "test-message"
    mocked_zsmq.recv.return_value = msg
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
    """Verify ZMQ_HOST takes priority over ZMQ_PORT

    Setting "host" will allow us to set the host, but the host will never be
    used (bug).

    Verify that the internal config class accepts host / port env vars
    appropriately.

    """

    msg = b"test-message"

    # The host set here *should* take priority over the env var, but it doesn't (bug).
    # The host is hardcoded to 0.0.0.0
    producer = ZMQProducer(host="redis", queue_name="test")

    assert producer.config["host"] == "test-host"
    assert producer.config["port"] == "5555"
    producer.produce(queue_name="test", message=msg)
    producer.shutdown()
