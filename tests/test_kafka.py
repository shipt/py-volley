from engine.data_models import BundleMessage
from engine.rsmq import BundleProducer


def test_kafka_producer(
    mock_kafka_producer: BundleProducer, bundle_message: BundleMessage
) -> None:
    mock_kafka_producer.produce(queue_name="test", message=bundle_message.dict())
