import pytest

from volley.queues import Queue, config_to_queue_map
from volley.serializers.base import NullSerializer


def test_bad_type() -> None:
    q = Queue(
        name="test",
        value="value",
        schema=dict,
        type="kafka",
        consumer="consumer",
        producer="producer",
        serializer=NullSerializer,
    )

    with pytest.raises(TypeError):
        q.connect("BAD_TYPE")  # type: ignore


def test_config_to_queue_map_missing_attr(config_dict: dict[str, dict[str, str]]) -> None:
    """if a config is missing an attribute, like "type", should raise error"""
    queues = [{"name": "myqueue", "serializer": "disabled", "schema": "volley.data_models.ComponentMessage"}]
    with pytest.raises(KeyError):
        config_to_queue_map(queues)
