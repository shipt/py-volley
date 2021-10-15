from engine.consumer import Consumer
from engine.data_models import BundleMessage
from engine.producer import Producer


def test_kafka_producer(
    mock_kafka_producer: Producer, bundle_message: BundleMessage
) -> None:

    assert mock_kafka_producer.produce(queue_name="test", message=bundle_message)


def test_kafka_consumer_success(mock_kafka_consumer: Consumer) -> None:
    bundle_message = mock_kafka_consumer.consume("test-q")
    assert isinstance(bundle_message, BundleMessage)
