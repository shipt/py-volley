import json
import logging
from datetime import datetime
from typing import Any, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pytest import LogCaptureFixture, MonkeyPatch

from example.data_models import InputMessage, OutputMessage
from tests.test_connectors.test_kafka import KafkaMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.queues import DLQNotConfiguredError


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.kafka.KProducer")
@patch("volley.connectors.kafka.KConsumer")
def test_component_success(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
    )
    input_msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=input_msg)

    output_msg = OutputMessage.parse_obj(OutputMessage.schema()["examples"][0])
    # component returns "just none"

    @eng.stream_app
    def func(*args: ComponentMessage) -> List[Tuple[str, OutputMessage]]:
        return [("output-topic", output_msg)]

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
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=b'{"random": "message"}')

    # component returns "just none"
    @eng.stream_app
    def func(*args: ComponentMessage) -> None:
        return None

    with pytest.raises(DLQNotConfiguredError):
        func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_rsmq_component(mock_rsmq: MagicMock) -> None:
    m = {"uuid": str(uuid4())}
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
        return [("comp_1", out)]

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

    with pytest.raises(NameError):
        Engine(
            input_queue=input_queue,
            output_queues=output_queues.copy(),
            dead_letter_queue="wrong-DLQ",
            queue_config=config_dict,
        )

    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues.copy(),
        dead_letter_queue="dead-letter-queue",
        queue_config=config_dict,
    )

    assert eng.input_queue == input_queue
    assert eng.dead_letter_queue == "dead-letter-queue"

    # all queues listed in "config_dict" should be viable producer targets
    for queue in config_dict.keys():
        assert queue in eng.output_queues
        assert queue in eng.queue_map

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
def test_null_serializer_fail(
    mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]], caplog: LogCaptureFixture
) -> None:
    """disable serialization for a message off input-topic

    this should cause schema validation to fail
    """
    config_dict["input-topic"]["serializer"] = "disabled"

    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-topic"
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

    # serializer disable, schema validation will fail
    # but messages will route to DLQ with exceptions handles
    with caplog.at_level(logging.WARNING):
        func()
    # this is a WARNING level, because rollbar is swallowing the log locally
    # its coming from logger.exception in volley.data_models.schema_handler
    # should only be one warning log - for the DLQ
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"

    # do not specifiy the DLQ
    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues,
        queue_config=config_dict,
    )

    @eng.stream_app
    def func2(*args: Any) -> None:
        return None

    # we disabled serializer though, so it will be fail pydantic validation
    with pytest.raises(DLQNotConfiguredError):
        func2()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_engine_configuration_failures(mock_rsmq: MagicMock) -> None:
    m = {"uuid": str(uuid4())}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m),
    }
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True
    cfg = {
        "comp_1": {
            "value": "random_val",
            "type": "rsmq",
        }
    }

    # try to init on a output queue that does not exist
    with pytest.raises(NameError):
        Engine(input_queue="comp_1", output_queues=["DOES_NOT_EXIST", "comp_1"], queue_config=cfg)

    # try to init on a input queue that does not exist
    with pytest.raises(NameError):
        Engine(input_queue="DOES_NOT_EXIST", output_queues=["comp_1"], queue_config=cfg)

    # try to init on a DLQ that does not exist
    with pytest.raises(NameError):
        Engine(input_queue="comp_1", output_queues=["comp_1"], dead_letter_queue="DOES_NOT_EXIST", queue_config=cfg)

    # try to init when missing required attribute in config
    missing_cfg = cfg.copy()
    missing_cfg["comp_1"] = cfg["comp_1"].copy()
    del missing_cfg["comp_1"]["type"]
    with pytest.raises(KeyError):
        Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=missing_cfg)

    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg)

    @eng.stream_app
    def bad_return_queue(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
        out = ComponentMessage(hello="world")
        return [("DOES_NOT_EXIST", out)]

    # trying to return a message to a queue that does not exist
    with pytest.raises(NameError):
        bad_return_queue()

    eng2 = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg)

    @eng2.stream_app
    def bad_return_type(msg: ComponentMessage) -> Any:
        out = dict(hello="world")
        return [("comp_1", out)]

    # trying to return a message to a queue of the wrong type
    with pytest.raises(TypeError):
        bad_return_type()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_serialization_fail_to_dlq(mock_rsmq: MagicMock) -> None:
    rsmq_msg = {"id": 123, "message": {"key": datetime.now()}}
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True

    cfg = {
        "comp_1": {"value": "random_val", "type": "rsmq", "schema": "volley.data_models.ComponentMessage"},
        "DLQ": {"value": "random_val", "type": "rsmq", "schema": "volley.data_models.ComponentMessage"},
    }

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, dead_letter_queue="DLQ")

    @eng.stream_app
    def func(msg: ComponentMessage) -> Any:
        return [("comp_1", {"hello": "world"})]

    # this shouldnt raise anything, which should mean message made it to DLQ successfully
    # TODO find a way assert ^^
    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RSMQConsumer.on_fail")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_fail_produce(mock_rsmq: MagicMock, mocked_fail: MagicMock) -> None:
    m = {"uuid": str(uuid4())}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m),
    }
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute.side_effect = Exception()
    cfg = {"comp_1": {"value": "random_val", "type": "rsmq", "schema": "volley.data_models.ComponentMessage"}}

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg)

    @eng.stream_app
    def func(msg: ComponentMessage) -> Any:
        out = ComponentMessage(hello="world")
        return [("comp_1", out)]

    func()

    # assert that the on_fail was called
    assert mocked_fail.called


@patch("volley.connectors.rsmq.RSMQConsumer.on_fail")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_init_no_output(mock_rsmq: MagicMock, mocked_fail: MagicMock) -> None:
    cfg = {"comp_1": {"value": "random_val", "type": "rsmq", "schema": "volley.data_models.ComponentMessage"}}

    # cant produce anywhere, and thats ok
    eng = Engine(input_queue="comp_1", queue_config=cfg)
    assert eng.output_queues == []

    cfg["DLQ"] = {"value": "dlq-topic", "type": "kafka"}
    # DLQ should become an output, even without any outputs defined
    eng2 = Engine(input_queue="comp_1", dead_letter_queue="DLQ", queue_config=cfg)
    assert "DLQ" in eng2.output_queues


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.logging.logger.propagate", True)
@patch("volley.connectors.kafka.KConsumer")
def test_kafka_config_init(mock_consumer: MagicMock, caplog: LogCaptureFixture, monkeypatch: MonkeyPatch) -> None:
    """init volley with a kafka queue with user provided kafka config"""
    monkeypatch.delenv("KAFKA_BROKERS", raising=True)

    msg = b"""{"x":"y"}"""
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    consumer_group = str(uuid4())
    kafka_brokers = f"my_broker_{str(uuid4())}:29092"
    cfg = {
        "comp_1": {
            "value": "kafka.topic",
            "type": "kafka",
            "schema": "volley.data_models.ComponentMessage",
            "config": {"group.id": consumer_group, "bootstrap.servers": kafka_brokers},
        }
    }

    eng = Engine(
        input_queue="comp_1",
        queue_config=cfg,
    )

    @eng.stream_app
    def func(msg: ComponentMessage) -> None:
        return None

    with caplog.at_level(logging.INFO):
        func()
        # kafka connector prints out its raw config
        # consumer group should be in that text
        assert consumer_group in caplog.text
        assert kafka_brokers in caplog.text
