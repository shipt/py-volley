import json
from typing import Any, Callable, Generator, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tests.test_connectors.test_kafka import KafkaMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_component_return_none(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """
    eng = Engine(input_queue="input-queue", output_queues=["output-queue"])
    mock_consumer.return_value.poll = lambda x: KafkaMessage()

    # component returns "just none"
    @eng.stream_app
    def func(*args: ComponentMessage) -> None:
        return None

    func()

    # component returns None, deprecated method
    @eng.stream_app
    def func_depr(*args: ComponentMessage) -> List[Tuple[str, None]]:
        return [("n/a", None)]

    func_depr()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_rsmq_component(mock_rsmq: MagicMock) -> None:
    m = {"uuid": str(uuid4)}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m),
    }
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg

    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"])

    @eng.stream_app
    def hello_world(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
        msg_dict = msg.dict()
        unique_val = msg_dict["uuid"]
        out = ComponentMessage(hello="world", unique_val=unique_val)
        return [("output-queue", out)]

    # must not raise any exceptions
    hello_world()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.kafka.KProducer", MagicMock())
@patch("volley.connectors.kafka.KConsumer")
def test_init_from_dict(mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]]) -> None:
    from example.data_models import InputMessage

    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-queue"
    output_queues = list(config_dict.keys())
    eng = Engine(input_queue=input_queue, output_queues=output_queues, queue_config=config_dict)

    @eng.stream_app
    def func(*args: Any) -> None:
        return None

    func()
