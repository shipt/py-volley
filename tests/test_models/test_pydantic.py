import json
from uuid import uuid4

from pydantic import BaseModel

from volley.models.pydantic_model import (
    ComponentMessage,
    PydanticModelHandler,
    PydanticParserModelHandler,
)


def test_pydantic_parse() -> None:
    """validates functionality of pydantic parser

    bytes to model and back to bytes
    """

    msg = {"msg": str(uuid4())}

    bytes_msg = json.dumps(msg).encode("utf-8")
    parser = PydanticParserModelHandler()
    data_model = parser.construct(message=bytes_msg, schema=ComponentMessage)
    assert isinstance(data_model, BaseModel)
    assert data_model.msg == msg["msg"]  # type: ignore

    deconstructed = parser.deconstruct(data_model)
    assert deconstructed == bytes_msg


def test_pydantic() -> None:
    """validates pydantic model constructor

    dict to model, back to dict
    """
    msg = {"msg": str(uuid4())}
    parser = PydanticModelHandler()
    data_model = parser.construct(message=msg, schema=ComponentMessage)
    assert isinstance(data_model, BaseModel)
    assert data_model.msg == msg["msg"]  # type: ignore

    deconstructed = parser.deconstruct(data_model)
    assert deconstructed == msg
