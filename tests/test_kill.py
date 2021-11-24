import threading
from unittest.mock import MagicMock, patch

from example.input_worker import eng, main


@patch("volley.engine.METRICS_ENABLED", False)
@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.kafka.KConsumer", MagicMock())
def test_graceful_kill() -> None:
    t = threading.Thread(target=main, daemon=True)
    t.start()

    eng.killer.exit_gracefully(100, None)
    assert eng.killer.kill_now is True
    t.join(timeout=10.0)
    assert not t.is_alive()
