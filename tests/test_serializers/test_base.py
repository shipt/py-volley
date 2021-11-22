from volley.serializers.base import NullSerializer


def test_null_serialzer() -> None:
    """null serializer doesnt do anything"""

    msg = b"Hello world"
    ser = NullSerializer()

    deserialized = ser.deserialize(msg)
    assert msg is deserialized

    serialized = ser.serialize(msg)
    assert msg is serialized
