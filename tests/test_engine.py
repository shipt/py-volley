from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from volley.data_models import ComponentMessage
from volley.engine import engine, get_consumer, get_producer
from tests.test_connectors.test_kafka import KafkaMessage


@patch("volley.connectors.kafka.KConsumer")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_get_consumer(mock_redis, mock_kafka) -> None:  # type: ignore
    qname = "random-queue-name"
    for c in ["kafka", "rsmq"]:
        consumer = get_consumer(c, qname)
        assert consumer.queue_name == qname

    with pytest.raises(KeyError):
        consumer = get_consumer("non-existant-queue", qname)


@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_get_producer(mock_redis, mock_kafka) -> None:  # type: ignore
    qname = "random-queue-name"
    for p in ["kafka", "rsmq"]:
        producer = get_producer(p, qname)
        assert producer.queue_name == qname

    with pytest.raises(KeyError):
        producer = get_producer("non-existant-queue", qname)


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_engine(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    mock_consumer.return_value.poll = lambda x: KafkaMessage()

    @engine(input_queue="input-queue", output_queues=["output-queue"])
    def func(*args: ComponentMessage) -> List[Tuple[None, None]]:
        return [(None, None)]

    func()
