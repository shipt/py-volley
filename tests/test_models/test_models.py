from unittest.mock import patch

from pytest import LogCaptureFixture, raises

from volley.models.base import message_model_handler, model_message_handler
from volley.models.pydantic_model import GenericMessage, PydanticModelHandler
from volley.serializers import JsonSerialization


def test_message_to_model_handler_fail() -> None:
    msg = b""""bad":"json"}"""
    ser = JsonSerialization()
    schema = GenericMessage
    model_handler = PydanticModelHandler()

    _msg, status = message_model_handler(message=msg, schema=schema, model_handler=model_handler, serializer=ser)

    # serialization failure should return raw message and failure status
    assert _msg == msg
    assert status is False


@patch("volley.logging.logger.propagate", True)
def test_model_to_message_handler_fail(caplog: LogCaptureFixture) -> None:
    """force errors within the data model to message handling"""

    with raises(Exception):
        model_message_handler(
            data_model=None, model_handler="bad_handler", serializer=None  # type: ignore  # passing bad data
        )

    with raises(Exception):
        model_message_handler(
            data_model=None, model_handler=None, serializer="bad_serializer"  # type: ignore  # passing bad data
        )


def test_message_to_model_handler_success() -> None:
    msg = b"""{"good":"json"}"""
    ser = JsonSerialization()
    schema = GenericMessage
    model_handler = PydanticModelHandler()

    handled_model, status = message_model_handler(
        message=msg, schema=schema, model_handler=model_handler, serializer=ser
    )
    assert status is True
    assert handled_model == GenericMessage.model_validate_json(msg)

    # model, schema, serializer disabled should also succeed
    handled_model, status = message_model_handler(message=msg, schema=None, model_handler=None, serializer=None)
    assert handled_model == msg
    assert status is True


def test_model_to_message_handler_success() -> None:
    msg = b"""{"good": "json"}"""
    data_model = GenericMessage.model_validate_json(msg)
    ser = JsonSerialization()
    model_handler = PydanticModelHandler()

    handled = model_message_handler(data_model=data_model, model_handler=model_handler, serializer=ser)

    assert handled == msg

    # model, schema, serializer disabled should also succeed
    handled = model_message_handler(data_model=data_model, model_handler=None, serializer=None)
    assert handled == data_model
