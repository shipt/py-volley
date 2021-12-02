"""handles tests for both base json and orjson serializers"""
from json import JSONDecodeError
from typing import List
from uuid import uuid4

import pytest
from msgpack.exceptions import ExtraData

from volley.serializers.base import BaseSerialization
from volley.serializers.json_serializer import JsonSerialization
from volley.serializers.msgpack_serializer import MsgPackSerialization
from volley.serializers.orjson_serializer import OrJsonSerialization


class CannotBeString:
    """an object that cannot be cast to string"""

    def __str__(self) -> None:  # type: ignore
        pass


@pytest.fixture
def serializers() -> List[BaseSerialization]:
    return [JsonSerialization(), OrJsonSerialization(), MsgPackSerialization()]


def test_interface(serializers: List[BaseSerialization]) -> None:
    for serializer in serializers:
        assert isinstance(serializer, BaseSerialization)


def test_success(serializers: List[BaseSerialization]) -> None:
    msg = {"hello": f"world-{uuid4()}"}

    for serializer in serializers:
        serialized = serializer.serialize(msg)
        assert isinstance(serialized, bytes)

        deserialized = serializer.deserialize(serialized)
        assert deserialized == msg


def test_fail(serializers: List[BaseSerialization]) -> None:
    msg = {"time": CannotBeString(), "number": 42}

    for serializer in serializers:
        with pytest.raises(TypeError):
            serializer.serialize(msg)

        bad_json = b"abc : 123}"
        with pytest.raises((JSONDecodeError, ExtraData)):
            serializer.deserialize(bad_json)

        non_str = CannotBeString()
        with pytest.raises((JSONDecodeError, TypeError)):  # type: ignore
            serializer.deserialize(non_str)  # type: ignore
