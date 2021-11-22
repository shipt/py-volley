from datetime import datetime
from json import JSONDecodeError

import pytest

from volley.serializers.base import BaseSerialization
from volley.serializers.json_serializer import JsonSerialization


def test_protocol() -> None:
    assert issubclass(JsonSerialization, BaseSerialization)


def test_success() -> None:
    serializer = JsonSerialization()

    msg = {"hello": "world", "number": 42}

    serialized = serializer.serialize(msg)
    assert isinstance(serialized, bytes)

    deserialized = serializer.deserialize(serialized)

    assert deserialized == msg


def test_fail() -> None:
    serializer = JsonSerialization()

    msg = {"time": datetime.now(), "number": 42}
    with pytest.raises(TypeError):
        serializer.serialize(msg, default=None)

    bad_json = "abc : 123}"
    with pytest.raises(JSONDecodeError):
        serializer.deserialize(bad_json)
