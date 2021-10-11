import os
from unittest.mock import patch

from pytest import fixture

from engine.data_models import BundleMessage
from engine.kafka import BundleConsumer as kafka_consumer
from engine.kafka import BundleProducer as kafka_producer
from engine.rsmq import BundleConsumer as rsmq_consumer
from engine.rsmq import BundleProducer as rsmq_producer

os.environ["INPUT_QUEUE"] = "input"
os.environ["OUTPUT_QUEUE"] = "output"
os.environ["REDIS_HOST"] = "redis"


@fixture
def bundle_message() -> BundleMessage:
    yield BundleMessage(
        message_id="123", params={}, message={"event_id": 123, "orders": [1, 2, 3]}
    )


@fixture
def mock_rsmq_producer() -> rsmq_producer:
    with patch("engine.rsmq.RedisSMQ"):
        producer = rsmq_producer(
            host="redis",
            queue_name="test",
        )
        yield producer


@fixture
def mock_rsmq_consumer() -> rsmq_consumer:
    with patch("engine.rsmq.RedisSMQ"):
        consumer = rsmq_consumer(
            host="redis",
            queue_name="test",
        )
        yield consumer


@fixture
def mock_kafka_consumer() -> kafka_consumer:
    with patch("engine.kafka.KafkaProducer"):
        producer = kafka_consumer(host="kafka", queue_name="test")
        yield producer


@fixture
def mock_kafka_producer() -> kafka_producer:
    with patch("engine.kafka.KafkaProducer"):
        producer = kafka_producer(host="kafka", queue_name="test")
        yield producer
