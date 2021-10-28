from typing import Any, Dict
from unittest.mock import patch

import pytest

from components.collector import main as collector
from components.data_models import (
    CollectFallback,
    CollectOptimizer,
    CollectTriage,
    InputMessage,
    OutputMessage,
    PublisherMessage,
    TriageMessage,
)
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.publisher import main as publisher
from components.triage import main as triage
from engine.data_models import ComponentMessage


def test_features(input_message: InputMessage, fp_service_response: Dict[str, Any]) -> None:
    with patch("components.features.requests.get") as fp_success:
        fp_success.return_value.status_code = 200
        fp_success.return_value.json = lambda: fp_service_response
        outputs = features.__wrapped__(input_message)

        for qname, message in outputs:
            assert qname == "triage"
            assert isinstance(message, TriageMessage)
            assert isinstance(message.enriched_orders, list)

            for order in message.enriched_orders:
                assert order["order_id"] in input_message.orders
                # spot check some attributes exist
                assert isinstance(order["delv_longitude"], float)
                assert isinstance(order["delv_latitude"], float)
                assert order["item_qty"] > 0


def test_bunk_order_id(bunk_input_message: InputMessage) -> None:
    with pytest.raises(Exception):
        outputs = features.__wrapped__(bunk_input_message)  # NOQA: F841


def test_bunk_fp_response(input_message: InputMessage) -> None:
    with pytest.raises(KeyError):
        with patch("components.features.requests.get") as bunk_fp_response:
            bunk_fp_response.return_value.status_code = 200
            bunk_fp_response.return_value.json = lambda: {"order_id": 1}
            outputs = features.__wrapped__(input_message)  # NOQA: F841


def test_triage(input_message: InputMessage) -> None:
    triage_message = features.__wrapped__(input_message)[0][1]
    outputs = triage.__wrapped__(triage_message)
    known_out_queues = ["fallback", "collector", "optimizer"]

    for qname, message in outputs:
        assert qname in known_out_queues
        assert isinstance(message, ComponentMessage)


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


def test_publisher(publisher_message: PublisherMessage) -> None:
    t_outputs = publisher.__wrapped__(publisher_message)
    for qname, m in t_outputs:
        assert m.optimizer_type == "optimizer"
        assert isinstance(m, OutputMessage)


def test_collector_publisher(
    collector_optimizer_message: CollectOptimizer,
    collector_fallback_message: CollectFallback,
    collector_triage_message: CollectTriage,
) -> None:
    f = collector.__wrapped__(collector_fallback_message)
    o = collector.__wrapped__(collector_optimizer_message)
    t = collector.__wrapped__(collector_triage_message)
    for i in [f, o, t]:
        for _i in i:
            assert _i[0] == "publisher"
