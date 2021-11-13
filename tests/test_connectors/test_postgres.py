from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

from volley.connectors import PGConsumer, PGProducer
from volley.data_models import ComponentMessage, QueueMessage


class MockExecute:
    def __init__(self, values: Optional[List[Any]] = None, *args: Any, **kwargs: Any) -> None:
        if not values:
            self._mapping = []
        else:
            self._mapping = values

    def execute(self) -> Any:
        return self


@patch("volley.connectors.postgres.Session")
@patch("volley.connectors.postgres.get_eng")
def test_pg_consumer(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    assert pg.delete_message("mock_queue", "mock_id")
    pg.on_fail()
    pg.shutdown()


@patch("volley.connectors.postgres.RUN_ONCE", True)
@patch("volley.connectors.postgres.Session")
@patch("volley.connectors.postgres.get_eng")
def test_pg_consume_success(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    mock_session.return_value.execute = lambda x: [MockExecute(values=[1, 2, 3])]
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    result_set = pg.consume()
    assert result_set


@patch("volley.connectors.postgres.Session")
@patch("volley.connectors.postgres.get_eng")
def test_pg_consume_fail(mock_eng: MagicMock, mock_session: MagicMock) -> None:
    mock_session.return_value.execute = lambda x: [MockExecute()]
    pg = PGConsumer(host="mockhost", queue_name="mock-queue")
    result_set = pg.consume()
    assert isinstance(result_set, QueueMessage)


@patch("volley.connectors.postgres.Session")
@patch("volley.connectors.postgres.get_eng")
def test_pg_producer(
    mock_eng: MagicMock,
    mock_session: MagicMock,
) -> None:
    pg = PGProducer(host="mockhost", queue_name="mock-queue")
    m = ComponentMessage.parse_obj(
        {
            "data": "full_of_data",
            "event_type": "optimizer",
            "bundle_request_id": "abc-123",
            "engine_event_id": "123-abc"
        }
    )
    msg = QueueMessage(message_id="mock", message=m)
    resp = pg.produce(queue_name="mock_q", message=msg)
    assert resp is True

    pg.shutdown()
