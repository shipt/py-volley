from typing import Dict, Type

import pytest
from pydantic.main import BaseModel

from volley.config import load_yaml
from volley.data_models import QueueMessage
from volley.queues import (
    Queue,
    apply_defaults,
    available_queues,
    config_to_queue_map,
    dict_to_config,
    import_module_from_string,
    interpolate_kafka_topics,
    yaml_to_dict_config,
)


def test_load_yaml_success() -> None:
    d = load_yaml("./example/volley_config.yml")
    assert "queues" in d
    assert isinstance(d, dict)


def test_load_yaml_fail() -> None:
    with pytest.raises(FileNotFoundError):
        load_yaml("donotexist")


def test_available_queues() -> None:
    all_queues: Dict[str, Queue] = available_queues("./example/volley_config.yml")

    for qname, q in all_queues.items():
        assert isinstance(qname, str)
        assert isinstance(q, Queue)


def test_yaml_to_dict_config() -> None:
    config = yaml_to_dict_config(yaml_path="./example/volley_config.yml")
    assert isinstance(config, dict)
    for q in config["queues"]:
        assert isinstance(q, dict)
        assert q["name"]
        assert q["value"]


def test_dict_to_config(config_dict: dict[str, dict[str, str]]) -> None:
    d = dict_to_config(config_dict)
    assert d["queues"]
    for q in d["queues"]:
        assert q["name"]
        assert q["type"]


def test_apply_defaults(config_dict: dict[str, dict[str, str]]) -> None:
    """assert global defaults get applied when not specified"""
    del config_dict["input-topic"]["schema"]
    config = dict_to_config(config_dict)
    defaulted = apply_defaults(config)
    for q in defaulted["queues"]:
        if q["type"] == "kafka":
            assert q["producer"] == "volley.connectors.kafka.KafkaProducer"
            assert q["consumer"] == "volley.connectors.kafka.KafkaConsumer"
            assert q["schema"] == "volley.data_models.ComponentMessage"


def test_config_to_queue_map(config_dict: dict[str, dict[str, str]]) -> None:
    config = dict_to_config(config_dict)
    defaulted = apply_defaults(config)
    queue_map = config_to_queue_map(defaulted["queues"])
    for queue_name, queue_obj in queue_map.items():
        assert isinstance(queue_obj, Queue)
        assert queue_obj.name == queue_name


def test_import_module_from_string() -> None:
    class_module = import_module_from_string("volley.data_models.QueueMessage")

    instance = class_module(message_id="abc", message={"data": "message"})

    assert issubclass(class_module, BaseModel)
    assert isinstance(instance, QueueMessage)


def test_interpolate_kafka_topics() -> None:
    templated = "{{ env }}.kafka.input"
    cfg = {"type": "kafka", "value": templated}
    interpolated = interpolate_kafka_topics(cfg)

    assert interpolated["value"] == "localhost.kafka.input"


def test_bad_connector_config(config_dict: dict[str, dict[str, str]]) -> None:
    """asserts TypeError raised when malformed connector config provided"""
    # from dict
    config_dict["input-topic"]["config"] = "bad_configuration"  # this needs to be a dict
    config = dict_to_config(config_dict)
    defaulted = apply_defaults(config)
    with pytest.raises(TypeError):
        config_to_queue_map(defaulted["queues"])

    # from yaml
    cfg = yaml_to_dict_config(yaml_path="./example/volley_config.yml")
    cfg["queues"][0]["config"] = "bad_configuration"
    defaulted = apply_defaults(cfg)
    with pytest.raises(TypeError):
        config_to_queue_map(defaulted["queues"])


def test_missing_queue_attr(config_dict: dict[str, dict[str, str]]) -> None:
    del config_dict["input-topic"]["value"]
    config = dict_to_config(config_dict)
    defaulted = apply_defaults(config)

    with pytest.raises(KeyError):
        config_to_queue_map(defaulted["queues"])
