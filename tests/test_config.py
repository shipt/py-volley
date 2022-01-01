import pytest
from pydantic.main import BaseModel

from volley.config import load_yaml
from volley.data_models import QueueMessage
from volley.profiles import Profile
from volley.queues import Queue, import_module_from_string


def test_load_yaml_success() -> None:
    d = load_yaml("./example/volley_config.yml")
    assert "queues" in d
    assert isinstance(d, dict)


def test_load_yaml_fail() -> None:
    with pytest.raises(FileNotFoundError):
        load_yaml("donotexist")


def test_import_module_from_string() -> None:
    class_module = import_module_from_string("volley.data_models.QueueMessage")

    instance = class_module(message_id="abc", message={"data": "message"})

    assert issubclass(class_module, BaseModel)
    assert isinstance(instance, QueueMessage)


def test_bad_connector_config(confluent_consumer_profile: Profile) -> None:
    """asserts error raised when malformed connector config provided
    the connector config must be a dict
    """
    with pytest.raises(TypeError):
        Queue(
            name="test",
            value="long_value",
            profile=confluent_consumer_profile,
            pass_through_config="bad_value",  # type: ignore
        )
