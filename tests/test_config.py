from typing import Any, Dict

import pytest
from pydantic.main import BaseModel

from volley.config import QueueConfig, load_yaml
from volley.data_models import QueueMessage
from volley.queues import import_module_from_string


def test_load_yaml_success() -> None:
    d = load_yaml("./example/volley_config.yml")
    assert "queues" in d
    assert isinstance(d, dict)


def test_load_yaml_fail() -> None:
    with pytest.raises(FileNotFoundError):
        load_yaml("donotexist")


def test_import_module_from_string() -> None:
    class_module = import_module_from_string("volley.data_models.QueueMessage")

    instance = class_module(message_context="abc", message={"data": "message"})

    assert issubclass(class_module, BaseModel)
    assert isinstance(instance, QueueMessage)


def test_typed_config() -> None:
    """initialize single queue config"""
    cfg = QueueConfig(name="test-cfg", value="my-queue", profile="confluent", config={"random": "configValue"})
    cfg_dict = cfg.to_dict()
    for key in ["model_handler", "consumer", "producer", "model_handler", "data_model", "serializer"]:
        assert key not in cfg_dict
    assert "profile" in cfg_dict
    assert "config" in cfg_dict


def test_typed_config_init(config_dict: Dict[str, Dict[str, Any]]) -> None:
    # : Dict[str, Dict[str, str]]
    configs = {}
    for _, v in config_dict.items():
        _cfg = QueueConfig(**v).to_dict()
        configs[_cfg["name"]] = _cfg
    assert configs == config_dict
