import json

from volley.models.proto_model import ProtoModelHandler
from tests.protos.compiled import messages_pb2


def test_proto() -> None:
    """validates proto"""

    p = messages_pb2.Person()
    p.name = "volley"

    ph = p.phones.add()
    ph.number = "1234567890"
    ph.type = messages_pb2.Person.PhoneType.HOME

    pmh = ProtoModelHandler()

    b = pmh.deconstruct(p)
    assert type(b) == bytes

    p2: messages_pb2.Person = pmh.construct(b, messages_pb2.Person)

    assert type(p2) == messages_pb2.Person
    assert p == p2
