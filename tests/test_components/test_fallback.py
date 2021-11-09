from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from components.data_models import CollectFallback, EnrichedOrder, OptimizerMessage
from components.fallback import main as optimizer


def mock_optimizer(orders: List[EnrichedOrder]) -> Dict[str, Any]:
    """dummy optimizer - creates one giant bundle"""
    return {
        "bundle_request_id": "string",
        "bundles": [{"group_id": "group-id-1", "orders": [x.order_id for x in orders]}],
    }


@patch("components.fallback.requests.post")
def test_optimizer(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200

    msg = OptimizerMessage(**OptimizerMessage.schema()["examples"][0])
    expected_response = mock_optimizer(msg.grouped_orders[0])

    mock_post.return_value.json = lambda: expected_response
    outputs = optimizer.__wrapped__(msg)

    for qname, output in outputs:
        assert isinstance(output, CollectFallback)
        assert output.event_type == "fallback"


@patch("components.fallback.requests.post")
def test_optimizer_fail(mock_post: MagicMock) -> None:
    """optimizer failure - everything should be bundle of one"""
    mock_post.return_value.status_code = 500
    mock_post.return_value.json = lambda: None

    msg = OptimizerMessage(**OptimizerMessage.schema()["examples"][0])

    all_order_ids = []
    for group in msg.grouped_orders:
        for order in group:
            all_order_ids.append(order.order_id)

    if msg.error_orders:
        for order in msg.error_orders:  # type: ignore
            all_order_ids.append(order.order_id)

    outputs = optimizer.__wrapped__(msg)

    for qname, output in outputs:
        assert isinstance(output, CollectFallback)
        assert output.event_type == "fallback"
        all_bundles = output.fallback_results["bundles"]

        # should only be bundles of 1 when optimizer fails
        assert len(all_order_ids) == len(all_bundles)
        for bundle in all_bundles:
            assert len(bundle.orders) == 1
