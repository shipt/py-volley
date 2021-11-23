import json
from typing import Any, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from example.data_models import InputMessage, OutputMessage
from tests.test_connectors.test_kafka import KafkaMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.queues import DLQ_NotConfiguredError


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_component_success(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """

    eng = Engine(
        input_queue="input-queue",
        output_queues=["output-queue"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
    )
    input_msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=input_msg)

    output_msg = OutputMessage.parse_obj(OutputMessage.schema()["examples"][0])
    # component returns "just none"

    @eng.stream_app
    def func(*args: ComponentMessage) -> List[Tuple[str, OutputMessage]]:
        return [("output-queue", output_msg)]

    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_component_return_none(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
    )
    msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)

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
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_dlq_not_implemented(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """
    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue=None,
    )
    mock_consumer.return_value.poll = lambda x: KafkaMessage()

    # component returns "just none"
    @eng.stream_app
    def func(*args: ComponentMessage) -> None:
        return None

    with pytest.raises(DLQ_NotConfiguredError):
        func()


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
    cfg = {
        "comp_1": {
            "name": "comp_1",
            "value": "random_val",
            "type": "rsmq",
        }
    }
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg)

    @eng.stream_app
    def hello_world(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
        msg_dict = msg.dict()
        unique_val = msg_dict["uuid"]
        out = ComponentMessage(hello="world", unique_val=unique_val)
        return [("output-topic", out)]

    # must not raise any exceptions
    hello_world()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.kafka.KProducer", MagicMock())
@patch("volley.connectors.kafka.KConsumer")
def test_init_from_dict(mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]]) -> None:

    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-topic"
    output_queues = list(config_dict.keys())
    eng = Engine(input_queue=input_queue, output_queues=output_queues, queue_config=config_dict)

    # use a function that returns None
    # not to be confused with a consumer that returns None
    @eng.stream_app
    def func(*args: Any) -> None:
        return None

    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.kafka.KProducer", MagicMock())
@patch("volley.connectors.kafka.KConsumer")
def test_null_serializer_fail(mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]]) -> None:
    """disable serialization for a message off input-queue"""
    config_dict["input-queue"]["serializer"] = "disabled"

    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-queue"
    output_queues = list(config_dict.keys())
    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues,
        queue_config=config_dict,
        dead_letter_queue="dead-letter-queue",
    )

    @eng.stream_app
    def func(*args: Any) -> None:
        return None

    # model on component expects data to be serialized to dict
    # we disabled serializer though, so it will be bytes
    # with pytest.raises(TypeError):
    func()

    # del func
    # # do not specifiy the DLQ
    # # serialization will fail
    # eng = Engine(
    #     input_queue=input_queue,
    #     output_queues=output_queues,
    #     queue_config=config_dict,
    # )
    # @eng.stream_app
    # def func2(*args: Any) -> None:
    #     return None

    # # model on component expects data to be serialized to dict
    # # we disabled serializer though, so it will be bytes
    # with pytest.raises(TypeError):
    #     func2()
