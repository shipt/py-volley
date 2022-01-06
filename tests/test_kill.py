import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

from example.input_worker import eng


@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.Consumer", MagicMock())
def test_graceful_kill() -> None:
    @eng.stream_app
    def func(*args: Any) -> bool:  # pylint: disable=W0613
        return True

    t = threading.Thread(target=func, daemon=True)
    t.start()

    time.sleep(1)
    eng.killer.exit_gracefully(100, None)
    assert eng.killer.kill_now is True
    t.join(timeout=10.0)
    assert not t.is_alive()
