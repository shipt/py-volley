from unittest.mock import MagicMock, patch

from volley.connectors import ZMQConsumer, ZMQProducer
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


@patch("volley.connectors.zmq._socket")
def test_zmqproducer(mocked_zsmq: MagicMock) -> None:  # pylint: disable=W0613
    msg = b"test-message"
    producer = ZMQProducer(host="redis", queue_name="test", config={"port": 5555})
    producer.produce(queue_name="test", message=msg)
    producer.shutdown()
