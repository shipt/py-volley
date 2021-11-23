from unittest.mock import MagicMock, patch

from pytest import fixture, raises

from volley.serializers.base import NullSerializer, handle_serializer


@fixture
def null_serializer() -> NullSerializer:
    return NullSerializer()


def test_null_serialzer() -> None:
    """null serializer doesnt do anything"""

    msg = b"Hello world"
    ser = NullSerializer()

    deserialized = ser.deserialize(msg)
    assert msg is deserialized

    serialized = ser.serialize(msg)
    assert msg is serialized


@patch("volley.serializers.base.NullSerializer")
def test_handle_serializer_fail(serializer: MagicMock) -> None:
    serializer.serialize.side_effect = Exception()
    serializer.deserialize.side_effect = Exception()

    raw_msg = b"abc"
    for operation in ["deserialize", "serialize"]:
        msg, status = handle_serializer(serializer=serializer, operation=operation, message=raw_msg)
        assert msg == raw_msg
        assert status is False

    with raises(NotImplementedError):
        handle_serializer(serializer=serializer, operation="xtz", message=raw_msg)
