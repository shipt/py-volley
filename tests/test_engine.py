from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from volley.data_models import ComponentMessage
from volley.engine import Engine
from tests.test_connectors.test_kafka import KafkaMessage
from unittest.mock import patch

from uuid import uuid4
import json


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_kafka_component(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    eng = Engine(input_queue="input-queue", output_queues=["output-queue"])
    mock_consumer.return_value.poll = lambda x: KafkaMessage()

    @eng.stream_app
    def func(*args: ComponentMessage) -> None:
        return None
    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_rsmq_component(mock_rsmq) -> None:
    m = {"uuid": str(uuid4)}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m),
    }
    mock_rsmq.return_value.receiveMessage\
        .return_value.exceptions\
        .return_value.execute = lambda: rsmq_msg
        
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"])

    @eng.stream_app
    def hello_world(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
        unique_val = msg.uuid
        out = ComponentMessage(hello="world" , unique_val=unique_val)
        return [("output-queue",out)]
    
    # must not raise any exceptions
    hello_world()
