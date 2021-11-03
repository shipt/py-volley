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
    assert metro_result["store_location_latitude"] == 42.9967809
    assert metro_result["store_location_longitude"] == -85.59336449999999


def test_features(input_message: InputMessage, fp_service_response: Dict[str, Any]) -> None:
    with patch("components.features.requests.get") as fp_success:
        fp_success.return_value.status_code = 200
        fp_success.return_value.json = lambda: fp_service_response
        outputs = features.__wrapped__(input_message)

        for qname, message in outputs:
            assert qname == "triage"
            assert isinstance(message, TriageMessage)
            assert isinstance(message.enriched_orders, list)

            for enr_order in message.enriched_orders:
                assert enr_order.order_id in input_message.orders
                # spot check some attributes exist
                assert isinstance(enr_order.delv_longitude, float)
                assert isinstance(enr_order.delv_latitude, float)
                assert enr_order.item_qty > 0


@patch("components.features.requests.get")
def test_bunk_fp_response(mock_get: MagicMock, input_message: InputMessage) -> None:
    mock_get.return_value.status_code = 500
    mock_get.return_value.json = lambda: {"order_id": 1}
    outputs = features.__wrapped__(input_message)  # NOQA: F841
    for qname, message in outputs:
        # forcing bad response from FP - so all should be "error orders"
        assert len(message.error_orders) == len(input_message.orders)
        assert len(message.enriched_orders) == 0
