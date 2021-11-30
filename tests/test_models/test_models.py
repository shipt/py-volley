from unittest.mock import patch

from pytest import LogCaptureFixture, raises

from volley.models.base import message_model_handler, model_message_handler
from volley.models.pydantic_model import ComponentMessage, PydanticModelHandler
from volley.serializers import JsonSerialization


def test_message_to_model_handler_fail() -> None:
    msg = b""""bad":"json"}"""
    ser = JsonSerialization()
    schema = ComponentMessage
    model_handler = PydanticModelHandler()

    with raises(Exception):
        # bad json should crash serializer
        message_model_handler(message=msg, schema=schema, model_handler=model_handler, serializer=ser)


@patch("volley.logging.logger.propagate", True)
def test_model_to_message_handler_fail(caplog: LogCaptureFixture) -> None:
    # force an error anyehere in the block
    with raises(Exception):
        # PydanticParserModelHandler expects no serialization
        model_message_handler(data_model=None, model_handler=None, serializer=None)  # type: ignore
    assert "failed transporting" in caplog.text
