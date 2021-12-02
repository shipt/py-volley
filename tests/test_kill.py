import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

from example.input_worker import eng


@patch("volley.engine.METRICS_ENABLED", True)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.kafka.KConsumer", MagicMock())
def test_graceful_kill() -> None:
    @eng.stream_app
    def func(*args: Any) -> None:  # pylint: disable=W0613
        return None

    t = threading.Thread(target=func, daemon=True)
    t.start()

    time.sleep(1)
    eng.killer.exit_gracefully(100, None)
    assert eng.killer.kill_now is True
    t.join(timeout=10.0)
    assert not t.is_alive()
