from engine.data_models import BundleMessage
from engine.rsmq import BundleConsumer, BundleProducer


def test_rsmq_producer(
    mock_rsmq_producer: BundleProducer, bundle_message: BundleMessage
) -> None:

    assert mock_rsmq_producer.produce(queue_name="test", message=bundle_message)


def test_rsmq_consumer(
    mock_rsmq_consumer: BundleConsumer, bundle_message: BundleMessage
) -> None:

    assert mock_rsmq_consumer.consume(queue_name="test")
