import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from components.data_models import InputMessage, TriageMessage
from components.features import get_metro_attr, get_shop_time
from components.features import main as features


def test_fp_default() -> None:
    fp_result = get_shop_time("16578146")
    assert fp_result["shop_time_minutes"] > 0


def test_get_metro_attr_default() -> None:
    metro_result = get_metro_attr("2110")
    assert metro_result["store_latitude"] == 42.9967809
    assert metro_result["store_longitude"] == -85.59336449999999


def mocked_requests_get(*args: Any, **kwargs: Any):  # type: ignore
    status_code = 200

    class MockResponse:
        def __init__(self, json_data: Dict[str, Any], status_code: int) -> None:
            self.json_data = json_data
            self.status_code = status_code

        def json(self) -> Dict[str, Any]:
            return self.json_data

    if "metro" in args[0]:
        with open("./tests/fixtures/metro_response.json", "r") as f:
            return MockResponse(json.load(f), status_code)
    if "flight" in args[0]:
        with open("./tests/fixtures/fp_service_response.json", "r") as f:
            return MockResponse(json.load(f), status_code)


@patch("components.features.requests.get", side_effect=mocked_requests_get)
def test_features(mocked_get: MagicMock, input_message: InputMessage) -> None:
    outputs = features.__wrapped__(input_message)

    all_order_ids = [o.order_id for o in input_message.orders]
    for qname, message in outputs:
        assert qname == "triage"
        assert isinstance(message, TriageMessage)
        assert isinstance(message.enriched_orders, list)

        for enr_order in message.enriched_orders:
            assert enr_order.order_id in all_order_ids
            assert enr_order.total_items >= 0


@patch("components.features.requests.get")
def test_external_call_error(mock_get: MagicMock, input_message: InputMessage) -> None:
    mock_get.status_code = 500

    outputs = features.__wrapped__(input_message)  # NOQA: F841
    for qname, message in outputs:
        # forcing bad response from FP - so all should be "error orders"
        assert len(message.error_orders) == len(input_message.orders)
        assert len(message.enriched_orders) == 0
