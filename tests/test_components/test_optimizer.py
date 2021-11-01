from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from components.data_models import CollectOptimizer, OptimizerMessage
from components.optimizer import main as optimizer


def mock_optimizer(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """dummy optimizer - creates one giant bundle"""
    return {
        "bundle_request_id": "string",
        "bundles": [{"group_id": "group-id-1", "orders": [x["order_id"] for x in orders]}],
    }


@patch("components.optimizer.requests.post")
def test_optimizer(mock_post: MagicMock) -> None:
    mock_post.return_value.status_code = 200

    msg = OptimizerMessage(**OptimizerMessage.schema()["examples"][0])
    expected_response = mock_optimizer(msg.grouped_orders[0])

    mock_post.return_value.json = lambda: expected_response
    outputs = optimizer.__wrapped__(msg)

    for qname, output in outputs:
        assert isinstance(output, CollectOptimizer)
        assert output.event_type == "optimizer"
