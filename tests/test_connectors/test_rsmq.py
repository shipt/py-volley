from unittest.mock import MagicMock, patch

from volley.connectors import RSMQConsumer, RSMQProducer
from volley.data_models import QueueMessage


def test_rsmq_producer(mock_rsmq_producer: RSMQProducer, bundle_message: QueueMessage) -> None:
    assert mock_rsmq_producer.produce(queue_name="test", message=bundle_message.json().encode("utf-8"))


def test_rsmq_consumer(mock_rsmq_consumer: RSMQConsumer) -> None:

    assert mock_rsmq_consumer.consume(queue_name="test")


def test_rsmq_delete(mock_rsmq_consumer: RSMQConsumer) -> None:

    assert mock_rsmq_consumer.delete_message(queue_name="test", message_id="abc123")


@patch("volley.connectors.rsmq.RedisSMQ")
def test_return_none(mocked_rsmq: MagicMock) -> None:
    mocked_rsmq.queue.receiveMessage.return_value.exceptions.return_value.execute = None
    consumer = RSMQConsumer(host="redis", queue_name="test")
    msg = consumer.consume(queue_name="test")
    assert msg is None
