from volley.connectors import RSMQConsumer, RSMQProducer
from volley.data_models import QueueMessage


def test_rsmq_producer(mock_rsmq_producer: RSMQProducer, bundle_message: QueueMessage) -> None:

    assert mock_rsmq_producer.produce(queue_name="test", message=bundle_message)


def test_rsmq_consumer(mock_rsmq_consumer: RSMQConsumer, bundle_message: QueueMessage) -> None:

    assert mock_rsmq_consumer.consume(queue_name="test")
