from typing import Optional
from unittest.mock import MagicMock, patch

from engine.consumer import Consumer
from engine.data_models import QueueMessage
from engine.kafka import BundleConsumer
from engine.producer import Producer


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


@patch("engine.kafka.KafkaConsumer")
def test_consume(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage()
    b = BundleConsumer(host="localhost", queue_name="input-queue")
    q_message = b.consume()
    assert isinstance(q_message, QueueMessage)


@patch("engine.kafka.RUN_ONCE", True)
@patch("engine.kafka.KafkaConsumer")
def test_consume_error(mock_consumer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage(error=True)
    b = BundleConsumer(host="localhost", queue_name="input-queue")
    q_message = b.consume()
    assert q_message is None
