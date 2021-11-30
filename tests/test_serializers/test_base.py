from pytest import fixture

from volley.serializers.base import NullSerializer


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
