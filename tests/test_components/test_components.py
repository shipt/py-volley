from typing import Any, Dict

from components.collector import main as collector
from components.data_models import CollectorMessage, OutputMessage
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.publisher import main as publisher
from components.triage import main as triage


def test_features(input_message: Dict[str, Any]) -> None:
    outputs = features.__wrapped__(input_message)
    for qname, message in outputs:
        assert qname == "triage"
        assert isinstance(message, dict)


def test_triage(input_message: Dict[str, Any]) -> None:
    triage_message = features.__wrapped__(input_message)[0][1]
    outputs = triage.__wrapped__(triage_message)
    known_out_queues = ["fallback", "collector", "optimizer"]

    for qname, message in outputs:
        assert qname in known_out_queues
        assert isinstance(message, dict)


def test_fallback_optimizer(input_message: Dict[str, Any]) -> None:
    triage_message = features.__wrapped__(input_message)[0][1]
    t_outputs = triage.__wrapped__(triage_message)
    outputs = None
    for qname, msg in t_outputs:
        if qname == "fallback":
            outputs = fallback.__wrapped__(msg)
    for qname, msg in t_outputs:
        if qname == "optimizer":
            outputs.extend(optimizer.__wrapped__(msg))  # type: ignore
    assert outputs is not None


def test_collector(collector_message: CollectorMessage) -> None:
    t_outputs = collector.__wrapped__(collector_message.dict())
    assert t_outputs


def test_publisher(collector_message: CollectorMessage) -> None:
    msg = {"results": [collector_message.dict()]}
    t_outputs = publisher.__wrapped__(msg)
    for qname, m in t_outputs:
        assert m["optimizer_type"] == "optimizer"
        assert OutputMessage(**m)

    msg["results"] = [collector_message.fallback_dict()]
    t_outputs = publisher.__wrapped__(msg)
    for qname, m in t_outputs:
        assert m["optimizer_type"] == "fallback"
        assert OutputMessage(**m)

    msg["results"] = [collector_message.optimizer_dict()]
    t_outputs = publisher.__wrapped__(msg)
    for qname, m in t_outputs:
        assert m["optimizer_type"] == "optimizer"
        assert OutputMessage(**m)


def test_collector_publisher(collector_message: CollectorMessage) -> None:
    f = collector.__wrapped__(collector_message.fallback_dict())
    o = collector.__wrapped__(collector_message.optimizer_dict())
    t = collector.__wrapped__(collector_message.triage_dict())
    for i in [f, o, t]:
        for _i in i:
            assert _i[0] == "publisher"
