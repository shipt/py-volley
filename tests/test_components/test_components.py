from typing import Any, Dict
from unittest.mock import MagicMock, patch

from components.data_models import InputMessage
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.triage import main as triage
from engine.data_models import ComponentMessage
from tests.test_components.test_features import mocked_requests_get


@patch("components.features.requests.get", side_effect=mocked_requests_get)
def test_triage(mock_get: MagicMock, input_message: InputMessage, fp_service_response: Dict[str, Any]) -> None:

    triage_message = features.__wrapped__(input_message)[0][1]
    outputs = triage.__wrapped__(triage_message)
    known_out_queues = ["fallback", "collector", "optimizer"]

    for qname, message in outputs:
        assert qname in known_out_queues
        assert isinstance(message, ComponentMessage)


@patch("components.features.requests.get", side_effect=mocked_requests_get)
def test_fallback_optimizer(
    mock_get: MagicMock, input_message: Dict[str, Any], fp_service_response: Dict[str, Any]
) -> None:
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
