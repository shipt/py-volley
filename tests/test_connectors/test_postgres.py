from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

from components.data_models import CollectFallback, CollectOptimizer, CollectTriage
from engine.connectors import PGConsumer, PGProducer
from engine.data_models import QueueMessage


class MockExecute:
    def __init__(self, values: Optional[List[Any]] = None, *args: Any, **kwargs: Any) -> None:
        if not values:
            self._mapping = []
        else:
            self._mapping = values

    def execute(self) -> Any:
        return self


@patch("engine.connectors.postgres.Session")
@patch("engine.connectors.postgres.get_eng")
def test_pg_consumer(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    assert pg.delete_message("mock_queue", "mock_id")
    pg.on_fail()
    pg.shutdown()


@patch("engine.connectors.postgres.RUN_ONCE", True)
@patch("engine.connectors.postgres.Session")
@patch("engine.connectors.postgres.get_eng")
def test_pg_consume_success(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    mock_session.return_value.execute = lambda x: [MockExecute(values=[1, 2, 3])]
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    result_set = pg.consume()
    assert result_set


@patch("engine.connectors.postgres.Session")
@patch("engine.connectors.postgres.get_eng")
def test_pg_consume_fail(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    mock_session.return_value.execute = lambda x: [MockExecute()]
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    result_set = pg.consume()
    assert isinstance(result_set, QueueMessage)


@patch("engine.connectors.postgres.Session")
@patch("engine.connectors.postgres.get_eng")
def test_pg_producer(
    mock_eng: MagicMock,
    mock_session: MagicMock,
    collector_optimizer_message: CollectOptimizer,
    collector_fallback_message: CollectFallback,
    collector_triage_message: CollectTriage,
) -> None:
    pg = PGProducer(host="mockhost", queue_name="mock-queue")

    for m in [collector_optimizer_message, collector_fallback_message, collector_triage_message]:
        msg = QueueMessage(message_id="mock", message=m)
        resp = pg.produce(queue_name="mock_q", message=msg)
        assert resp is True

    pg.shutdown()
