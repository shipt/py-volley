from components.data_models import QueueMessage
from engine.consumer import Consumer
from engine.producer import Producer


def test_kafka_producer(
    mock_kafka_producer: Producer, bundle_message: QueueMessage
) -> None:

    assert mock_kafka_producer.produce(queue_name="test", message=bundle_message)


def test_kafka_consumer_success(mock_kafka_consumer: Consumer) -> None:
    bundle_message = mock_kafka_consumer.consume("test-q")
    assert isinstance(bundle_message, QueueMessage)
