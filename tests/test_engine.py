import json
import logging
import threading
import time
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError
from pytest import LogCaptureFixture, MonkeyPatch

from example.data_models import InputMessage, OutputMessage
from tests.conftest import KafkaMessage
from volley.config import QueueConfig
from volley.data_models import GenericMessage
from volley.engine import Engine
from volley.queues import DLQNotConfiguredError


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.Producer.poll", MagicMock())
@patch("volley.connectors.confluent.Producer")
@patch("volley.connectors.confluent.Consumer")
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
    input_msg = json.dumps(InputMessage.model_json_schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=input_msg)

    output_msg = OutputMessage.model_validate(OutputMessage.model_json_schema()["examples"][0])
    # component returns "just none"

    @eng.stream_app
    def func(msg: Any) -> List[Tuple[str, OutputMessage]]:  # pylint: disable=W0613
        return [("output-topic", output_msg)]

    func()
    eng.shutdown()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.Producer")
@patch("volley.connectors.confluent.Consumer")
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
    msg = json.dumps(InputMessage.model_json_schema()["examples"][0]).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=msg)

    # component returns "just none"
    @eng.stream_app
    def func(*args: GenericMessage) -> bool:  # pylint: disable=W0613
        return True

    func()
    eng.shutdown()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.Producer")
@patch("volley.connectors.confluent.Consumer")
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

    eng.shutdown()


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
    def hello_world(msg: GenericMessage) -> List[Tuple[str, GenericMessage]]:
        msg_dict = msg.model_dump()
        unique_val = msg_dict["uuid"]
        out = GenericMessage(hello="world", unique_val=unique_val)
        return [("comp_1", out)]

    # must not raise any exceptions
    hello_world()
    eng.shutdown()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.Producer", MagicMock())
@patch("volley.connectors.confluent.Consumer")
def test_init_from_dict(mock_consumer: MagicMock, config_dict: Dict[str, Dict[str, str]]) -> None:
    data = InputMessage.model_json_schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=msg)
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
    eng.shutdown()


@patch("volley.logging.logger.propagate", True)
@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.Producer", MagicMock())
@patch("volley.connectors.confluent.Consumer")
def test_null_serializer_fail(
    mock_consumer: MagicMock, config_dict: Dict[str, Dict[str, str]], caplog: LogCaptureFixture
) -> None:
    """disable serialization for a message off input-topic
    this should cause schema validation to fail
    """
    config_dict["input-topic"]["serializer"] = "disabled"

    data = InputMessage.model_json_schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=msg)
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
    assert "pydantic_core._pydantic_core.ValidationError" in caplog.text
    assert "failed producing message to" not in caplog.text
    eng.shutdown()

    # do not specifiy the DLQ
    eng = Engine(input_queue=input_queue, output_queues=output_queues, queue_config=config_dict, metrics_port=None)

    @eng.stream_app
    def func2(*args: Any) -> bool:  # pylint: disable=W0613
        return True

    # with no DLQ configured, will raise DLQNotConfiguredError when
    # unhandled exception in serialization or model construction
    with pytest.raises(DLQNotConfiguredError):
        func2()
    eng.shutdown()


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
    def bad_return_queue(msg: GenericMessage) -> List[Tuple[str, GenericMessage]]:  # pylint: disable=W0613
        out = GenericMessage(hello="world")
        return [("DOES_NOT_EXIST", out)]

    # trying to return a message to a queue that does not exist
    with pytest.raises(KeyError):
        bad_return_queue()
    eng.shutdown()

    eng2 = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng2.stream_app
    def bad_return_type(msg: GenericMessage) -> Any:  # pylint: disable=W0613
        out = dict(hello="world")
        return [("comp_1", out)]

    # trying to return a message to a queue of the wrong type
    with pytest.raises(TypeError):
        bad_return_type()
    eng2.shutdown()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RedisSMQ")
def test_serialization_fail_crash(mock_rsmq: MagicMock, caplog: LogCaptureFixture) -> None:
    rsmq_msg = {"id": 123, "message": {"key": datetime.now()}}
    mock_rsmq.return_value.receiveMessage.return_value.exceptions.return_value.execute = lambda: rsmq_msg
    mock_rsmq.return_value.sendMessage.return_value.execute = lambda: True

    cfg = {
        "comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.GenericMessage"},
        "DLQ": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.GenericMessage"},
    }

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(
        input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, dead_letter_queue="DLQ", metrics_port=None
    )

    @eng.stream_app
    def func(msg: GenericMessage) -> Any:  # pylint: disable=W0613
        return [("comp_1", {"hello": "world"})]

    with pytest.raises(Exception):
        func()
        assert "Deserialization failed" in caplog.text
    eng.shutdown()


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
    cfg = {"comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.GenericMessage"}}

    # using comp_1 as a DLQ, just to make things run for the test
    eng = Engine(input_queue="comp_1", output_queues=["comp_1"], queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def func(msg: GenericMessage) -> Any:  # pylint: disable=W0613
        out = GenericMessage(hello="world")
        return [("comp_1", out)]

    func()

    # assert that the on_fail was called
    assert mocked_fail.called
    eng.shutdown()


@patch("volley.connectors.rsmq.RSMQConsumer.on_fail")
@patch("volley.connectors.rsmq.RedisSMQ")
def test_init_no_output(mock_rsmq: MagicMock, mocked_fail: MagicMock) -> None:  # pylint: disable=W0613
    cfg = {"comp_1": {"value": "random_val", "profile": "rsmq", "schema": "volley.data_models.GenericMessage"}}

    # cant produce anywhere, and thats ok
    eng = Engine(input_queue="comp_1", queue_config=cfg)
    assert eng.output_queues == []
    cfg["DLQ"] = {"value": "dlq-topic", "profile": "confluent"}
    # DLQ should become an output, even without any outputs defined
    eng2 = Engine(input_queue="comp_1", dead_letter_queue="DLQ", queue_config=cfg, metrics_port=None)
    assert "DLQ" in eng2.output_queues


@patch("volley.connectors.confluent.Producer", MagicMock())
@patch("volley.engine.RUN_ONCE", True)
@patch("volley.logging.logger.propagate", True)
@patch("volley.connectors.confluent.Consumer")
def test_kafka_config_init(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:
    """init volley with a kafka queue with user provided kafka config"""
    monkeypatch.delenv("KAFKA_BROKERS", raising=True)

    msg = b"""{"x":"y"}"""
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="kafka.topic", msg=msg)
    consumer_group = str(uuid4())
    kafka_brokers = f"my_broker_{str(uuid4())}:9092"
    cfg = {
        "comp_1": {
            "value": "kafka.topic",
            "profile": "confluent",
            "schema": "volley.data_models.GenericMessage",
            "config": {"group.id": consumer_group, "bootstrap.servers": kafka_brokers},
        }
    }

    eng = Engine(input_queue="comp_1", queue_config=cfg, metrics_port=None)

    @eng.stream_app
    def func(msg: GenericMessage) -> bool:  # pylint: disable=W0613
        return True

    func()

    assert consumer_group == eng.queue_map["comp_1"].pass_through_config["group.id"]
    assert kafka_brokers == eng.queue_map["comp_1"].pass_through_config["bootstrap.servers"]
    eng.shutdown()


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
    eng.shutdown()


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.Producer", MagicMock())
@patch("volley.connectors.confluent.Consumer")
def test_runtime_connector_configs(mock_consumer: MagicMock, config_dict: Dict[str, Dict[str, str]]) -> None:
    """test wrapped func can return variable length tuples"""
    data = InputMessage.model_json_schema()["examples"][0]
    msg = json.dumps(data).encode("utf-8")
    mock_consumer.return_value.poll = lambda x: KafkaMessage(topic="localhost.kafka.input", msg=msg)
    input_queue = "input-topic"
    output_queues = list(config_dict.keys())

    eng = Engine(
        input_queue=input_queue,
        output_queues=output_queues.copy(),
        dead_letter_queue="dead-letter-queue",
        queue_config=config_dict,
        metrics_port=None,
    )

    m = GenericMessage(hello="world")

    # define function the returns producer runtime configs
    @eng.stream_app
    def tuple_two(msg: Any) -> List[Tuple[str, GenericMessage, Dict[str, Any]]]:  # pylint: disable=W0613
        send_rsmq = ("comp_1", m, {"delay": 10})
        send_kafka = ("output-topic", m, {"key": "abc"})
        return [send_rsmq, send_kafka]

    # function must not raise
    tuple_two()
    eng.shutdown()


@patch("volley.connectors.confluent.Producer", MagicMock())
def test_invalid_queue(config_dict: Dict[str, Dict[str, str]]) -> None:
    """queue provided in the init parameters input_queue, output_queues, dead_letter_queue
    must also exist in configuration
    """

    # non-exist input queue
    with pytest.raises(KeyError) as err:
        _id = str(uuid4())
        Engine(
            input_queue=f"not_exist_{_id}",
            output_queues=list(config_dict.keys()),
            queue_config=config_dict,
            metrics_port=None,
        )
    assert _id in str(err.value)

    # non-exist output queue
    with pytest.raises(KeyError) as err:
        _id = str(uuid4())
        Engine(
            input_queue="input-topic",
            output_queues=[f"not_exist_{_id}"],
            queue_config=config_dict,
            metrics_port=None,
        )
    assert _id in str(err.value)

    # non-exist dead letter queue
    with pytest.raises(KeyError) as err:
        _id = str(uuid4())
        Engine(
            input_queue="input-topic",
            output_queues=["output-topic"],
            dead_letter_queue=f"not_exist_{_id}",
            queue_config=config_dict,
            metrics_port=None,
        )
    assert _id in str(err.value)


@patch("volley.engine.RUN_ONCE", True)
@patch("volley.connectors.confluent.Producer.poll", MagicMock())
@patch("volley.connectors.confluent.Producer", MagicMock())
@patch("volley.connectors.confluent.Consumer")
def test_pass_msg_ctx(
    mock_consumer: MagicMock,
) -> None:
    """client function defines `msg_ctx` and parameter and receives QueueMessage.message_context"""

    eng = Engine(
        input_queue="input-topic",
        output_queues=["output-topic"],
        yaml_config_path="./example/volley_config.yml",
        dead_letter_queue="dead-letter-queue",
        metrics_port=None,
    )
    input_msg = json.dumps(InputMessage.model_json_schema()["examples"][0]).encode("utf-8")
    kafka_msg = KafkaMessage(topic="localhost.kafka.input", msg=input_msg)
    mock_message = lambda x: kafka_msg  # noqa
    mock_consumer.return_value.poll = mock_message

    output_msg = OutputMessage.model_validate(OutputMessage.model_json_schema()["examples"][0])
    # component returns "just none"

    @eng.stream_app
    def func(msg: Any, msg_ctx: Any) -> List[Tuple[str, OutputMessage]]:
        assert msg == InputMessage.model_validate_json(input_msg)
        assert isinstance(msg_ctx, KafkaMessage)
        return [("output-topic", output_msg)]

    func()
    eng.shutdown()


@patch("volley.connectors.confluent.Producer", MagicMock())
def test_init_typedConfig(typedConfig_list: List[QueueConfig]) -> None:
    """init Engine from typed configuration object"""
    eng = Engine(
        input_queue="input-topic",
        output_queues=["comp_1", "output-topic"],
        dead_letter_queue="dead-letter-queue",
        queue_config=typedConfig_list,
    )
    assert eng.app_name


@patch("volley.connectors.confluent.Consumer")
def test_multiproc_metrics(mock_consumer: MagicMock, monkeypatch: MonkeyPatch) -> None:  # pylint: disable=W0613
    """test metrics server"""
    cfg = [QueueConfig(name="test-cfg", value="my-topic", profile="confluent")]
    port = 1233
    eng = Engine(
        input_queue="test-cfg",
        queue_config=cfg,
        poll_interval_seconds=0.1,
        metrics_port=port,
    )
    mock_consumer.return_value.poll = lambda x: KafkaMessage(msg=b'{"random":"message"}', topic="my-topic")

    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp")

    @eng.stream_app
    def func(args: Any) -> bool:  # pylint: disable=W0613
        return True

    t = threading.Thread(target=func, daemon=True)
    t.start()
    time.sleep(1)
    try:
        resp = urllib.request.urlopen(f"http://0.0.0.0:{port}/metrics")
        assert resp.status == 200
    finally:
        t.join(timeout=1.0)
