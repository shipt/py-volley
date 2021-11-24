from datetime import datetime
from json import JSONDecodeError
from uuid import uuid4

import pytest

from volley.serializers.base import BaseSerialization, handle_serializer
from volley.serializers.json_serializer import JsonSerialization


class CannotBeString:
    """an object that cannot be cast to string"""

    def __str__(self) -> None:  # type: ignore
        pass


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

    non_str = CannotBeString()
    with pytest.raises(TypeError):
        serializer.deserialize(non_str)


def test_handler_fail() -> None:
    raw_msg = b"abc"
    serializer = JsonSerialization()

    msg, status = handle_serializer(serializer=serializer, operation="deserialize", message=raw_msg)
    assert raw_msg == msg
    assert status is False

    non_str = CannotBeString()
    msg, status = handle_serializer(serializer=serializer, operation="serialize", message=non_str)
    assert msg == non_str
    assert status is False


def test_handler_success() -> None:
    serializer = JsonSerialization()
    raw_msg = {"hello": f"world-{uuid4()}"}

    ser_msg, status = handle_serializer(serializer=serializer, operation="serialize", message=raw_msg)
    assert ser_msg != raw_msg
    assert status is True

    deser_msg, status = handle_serializer(serializer=serializer, operation="deserialize", message=ser_msg)
    assert deser_msg == raw_msg
    assert status is True
