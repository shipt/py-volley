import json
import logging
from datetime import datetime
from typing import Any, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from pytest import LogCaptureFixture, MonkeyPatch

from example.data_models import InputMessage, OutputMessage
from tests.conftest import KafkaMessage

# from tests.test_connectors.test_kafka import KafkaMessage
from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.queues import DLQNotConfiguredError


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.KProducer")
@patch("volley.connectors.confluent.KConsumer")
def test_component_success(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:  # pylint: disable=W0613
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
        metrics_port=None,
    )
    input_msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=input_msg)

    output_msg = OutputMessage.parse_obj(OutputMessage.schema()["examples"][0])
    # component returns "just none"

    @eng.stream_app
    def func(msg: Any) -> List[Tuple[str, OutputMessage]]:  # pylint: disable=W0613
        return [("output-topic", output_msg)]

    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.KProducer")
@patch("volley.connectors.confluent.KConsumer")
def test_component_return_none(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:  # pylint: disable=W0613
    """test a stubbed component that does not produce messages
    passes so long as no exception is raised
    """

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
        metrics_port=None,
    )
    msg = json.dumps(InputMessage.schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)

    # component returns "just none"
    @eng.stream_app
    def func(*args: ComponentMessage) -> bool:  # pylint: disable=W0613
        return True

    func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.KProducer")
@patch("volley.connectors.confluent.KConsumer")
def test_dlq_not_implemented(mock_consumer: MagicMock, mock_producer: MagicMock) -> None:  # pylint: disable=W0613
    """test a stubbed component that does not produce messages"""
    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue=None,
        metrics_port=None,
    )
    # message will not adhere to input-topic message schema specified in yaml_config_path
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=b'{"random": "message"}')

    @eng.stream_app
    def func(args: Any) -> bool:  # pylint: disable=W0613
        return True

    with pytest.raises(DLQNotConfiguredError):
        func()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_rsmq_component(mock_rsmq: MagicMock) -> None:
    m = {"uuid": str(uuid4())}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m).encode("utf8"),
    }
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True
    cfg = {
        "comp_1": {
            "name": "comp_1",
            "value": "random_val",
            "profile": "rsmq",
        }
    }
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def hello_world(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:
        msg_dict = msg.dict()
        unique_val = msg_dict["uuid"]
        out = ComponentMessage(hello="world", unique_val=unique_val)
        return [("comp_1", out)]

    # must not raise any exceptions
    hello_world()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.KProducer", MagicMock())
@patch("volley.connectors.confluent.KConsumer")
def test_init_from_dict(mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]]) -> None:

    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-topic"
    output_queues = list(config_dict.keys())

    with pytest.raises(KeyError):
        Engine(
            input_queue=input_queue,
            output_queues=output_queues.copy(),
            dead_letter_queue="wrong-DLQ",
            queue_config=config_dict,
            metrics_port=None,
        )

    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues.copy(),
        dead_letter_queue="dead-letter-queue",
        queue_config=config_dict,
        metrics_port=None,
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
    def func(args: Any) -> bool:  # pylint: disable=W0613
        return True

    func()


@patch("volley.logging.logger.propagate", True)
@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.KProducer", MagicMock())
@patch("volley.connectors.confluent.KConsumer")
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
        metrics_port=None,
    )

    @eng.stream_app
    def func(args: Any) -> bool:  # pylint: disable=W0613
        return True

    # serializer disabled, schema validation will fail
    # but messages will route to DLQ with exceptions handled
    with caplog.at_level(logging.WARNING):
        func()

    assert "Failed model construction" in caplog.text
    assert "pydantic.error_wrappers.ValidationError" in caplog.text
    assert "failed producing message to" not in caplog.text

    # do not specifiy the DLQ
    eng = Engine(input_queue=input_queue, output_queues=output_queues, queue_config=config_dict, metrics_port=None)

    @eng.stream_app
    def func2(*args: Any) -> bool:  # pylint: disable=W0613
        return True

    # with no DLQ configured, will raise DLQNotConfiguredError when
    # unhandled exception in serialization or model construction
    with pytest.raises(DLQNotConfiguredError):
        func2()


@patch("volley.engine.RUN_ONCE", True)
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
            "profile": "rsmq",
        }
    }

    # try to init on a output queue that does not exist
    with pytest.raises(KeyError):
        Engine(input_queue="comp_1", output_queues=["DOES_NOT_EXIST", "comp_1"], queue_config=cfg, metrics_port=None)

    # try to init on a input queue that does not exist
    with pytest.raises(KeyError):
        Engine(input_queue="DOES_NOT_EXIST", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    # try to init on a DLQ that does not exist
    with pytest.raises(KeyError):
        Engine(
            input_queue="comp_1",
            output_queues=["comp_1"],
            dead_letter_queue="DOES_NOT_EXIST",
            queue_config=cfg,
            metrics_port=None,
        )

    # try to init when missing required attribute in config
    missing_cfg = cfg.copy()
    missing_cfg["comp_1"] = cfg["comp_1"].copy()
    del missing_cfg["comp_1"]["profile"]
    with pytest.raises(ValidationError):
        Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=missing_cfg, metrics_port=None)

    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def bad_return_queue(msg: ComponentMessage) -> List[Tuple[str, ComponentMessage]]:  # pylint: disable=W0613
        out = ComponentMessage(hello="world")
        return [("DOES_NOT_EXIST", out)]

    # trying to return a message to a queue that does not exist
    with pytest.raises(KeyError):
        bad_return_queue()

    eng2 = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng2.stream_app
    def bad_return_type(msg: ComponentMessage) -> Any:  # pylint: disable=W0613
        out = dict(hello="world")
        return [("comp_1", out)]

    # trying to return a message to a queue of the wrong type
    with pytest.raises(TypeError):
        bad_return_type()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_serialization_fail_crash(mock_rsmq: MagicMock, caplog: LogCaptureFixture) -> None:
    rsmq_msg = {"id": 123, "message": {"key": datetime.now()}}
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True

    cfg = {
        "comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.ComponentMessage"},
        "DLQ": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.ComponentMessage"},
    }

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(
        input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, dead_letter_queue="DLQ", metrics_port=None
    )

    @eng.stream_app
    def func(msg: ComponentMessage) -> Any:  # pylint: disable=W0613
        return [("comp_1", {"hello": "world"})]

    with pytest.raises(Exception):
        func()
        assert "Deserialization failed" in caplog.text


@patch("volley.engine.RUN_ONCE", True)
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
    cfg = {"comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.ComponentMessage"}}

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def func(msg: ComponentMessage) -> Any:  # pylint: disable=W0613
        out = ComponentMessage(hello="world")
        return [("comp_1", out)]

    func()

    # assert that the on_fail was called
    assert mocked_fail.called


@patch("volley.connectors.rsmq.RSMQConsumer.on_fail")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_init_no_output(mock_rsmq: MagicMock, mocked_fail: MagicMock) -> None:  # pylint: disable=W0613
    cfg = {"comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.ComponentMessage"}}

    # cant produce anywhere, and thats ok
    eng = Engine(input_queue="comp_1", queue_config=cfg)
    assert eng.output_queues == []

    cfg["DLQ"] = {"value": "dlq-topic", "profile": "confluent"}
    # DLQ should become an output, even without any outputs defined
    eng2 = Engine(input_queue="comp_1", dead_letter_queue="DLQ", queue_config=cfg, metrics_port=None)
    assert "DLQ" in eng2.output_queues


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.logging.logger.propagate", True)
@patch("volley.connectors.confluent.KConsumer")
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
            "profile": "confluent",
            "schema": "volley.data_models.ComponentMessage",
            "config": {"group.id": consumer_group, "bootstrap.servers": kafka_brokers},
        }
    }

    eng = Engine(input_queue="comp_1", queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def func(msg: ComponentMessage) -> bool:  # pylint: disable=W0613
        return True

    with caplog.at_level(logging.INFO):
        func()
        # kafka connector prints out its raw config
        # consumer group should be in that text
        assert consumer_group in caplog.text
        assert kafka_brokers in caplog.text


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.logging.logger.propagate", True)
@patch("volley.connectors.rsmq.RedisSMQ")
@patch("volley.engine.message_model_handler")
def test_wild_dlq_error(mock_handler: MagicMock, mock_rsmq: MagicMock, caplog: LogCaptureFixture) -> None:
    """test error level logs when message fails to successfully reach DLQ"""
    mock_handler.return_value = False, False
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: False

    m = {"uuid": str(uuid4())}
    rsmq_msg = {
        "id": "rsmq_id",
        "message": json.dumps(m),
    }
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    cfg = {
        "comp_1": {"value": "random_val", "profile": "rsmq"},
        "dlq": {"profile": "rsmq-dlq", "value": "my_dlq"},
    }

    eng = Engine(input_queue="comp_1", dead_letter_queue="dlq", queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def fun(msg: Any) -> bool:  # pylint: disable=W0613
        return True

    with caplog.at_level(logging.ERROR):
        fun()
    assert "failed producing message to dlq" in caplog.text


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.KProducer", MagicMock())
@patch("volley.connectors.confluent.KConsumer")
def test_runtime_connector_configs(mock_consumer: MagicMock, config_dict: dict[str, dict[str, str]]) -> None:
    """test wrapped func can return variable length tuples"""
    data = InputMessage.schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=msg)
    input_queue = "input-topic"
    output_queues = list(config_dict.keys())

    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues.copy(),
        dead_letter_queue="dead-letter-queue",
        queue_config=config_dict,
        metrics_port=None,
    )

    m = ComponentMessage(hello="world")

    # define function the returns producer runtime configs
    @eng.stream_app
    def tuple_two(msg: Any) -> List[Tuple[str, ComponentMessage, dict[str, Any]]]:  # pylint: disable=W0613
        send_rsmq = ("comp_1", m, {"delay": 10})
        send_kafka = ("output-topic", m, {"key": "abc"})
        return [send_rsmq, send_kafka]

    # function must not raise
    tuple_two()
