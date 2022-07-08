from typing import Dict

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
    assert cfg.name in list(cfg_dict.keys())[0]
    for key in ["model_handler", "consumer", "producer", "model_handler", "data_model", "serializer"]:
        assert key not in cfg_dict[cfg.name]
    assert "profile" in cfg_dict[cfg.name]
    assert "config" in cfg_dict[cfg.name]


def test_typed_config_init(config_dict) -> None:
    # : Dict[str, Dict[str, str]]
    configs = {}
    for k, v in config_dict.items():
        _cfg = QueueConfig(**v).to_dict()
        configs.update(_cfg)
    assert configs == config_dict
