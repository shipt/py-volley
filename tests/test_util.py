import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from example.input_worker import eng
from volley.util import FuncEnvelope


@patch("volley.connectors.rsmq.RSMQProducer", MagicMock())
@patch("volley.connectors.confluent.Consumer")
def test_graceful_kill(mock_consumer: MagicMock) -> None:
    mock_consumer.consume.return_value = None

    @eng.stream_app
    def func(*args: Any) -> bool:  # pylint: disable=W0613
        return True

    t = threading.Thread(target=func, daemon=True)
    t.start()

    time.sleep(2)
    eng.killer.exit_gracefully(100, None)
    assert eng.killer.kill_now is True
    t.join(timeout=10.0)
    assert not t.is_alive()


def test_func_envelope() -> None:
    """Test proper signature on wrapped function"""

    def fun0(m: Any, msg_ctx: Any) -> None:  # pylint: disable=W0613
        pass

    wrapped = FuncEnvelope(fun0)
    assert wrapped.needs_msg_ctx is True
    assert wrapped.is_coroutine is False
    assert wrapped.message_param == "m"

    # any order of params must work
    def fun1(msg_ctx: Any, message: Any) -> None:  # pylint: disable=W0613
        pass

    wrapped = FuncEnvelope(fun1)
    assert wrapped.needs_msg_ctx is True
    assert wrapped.is_coroutine is False
    assert wrapped.message_param == "message"

    # async function should be coroutine
    async def fun2(m: Any) -> None:  # pylint: disable=W0613
        pass

    wrapped = FuncEnvelope(fun2)
    assert wrapped.is_coroutine is True


def test_func_envelope_toomanyparam() -> None:
    """Test proper signature on wrapped function"""

    def fun(m: Any, msg_ctx: Any, extra: Any) -> None:  # pylint: disable=W0613
        pass

    with pytest.raises(TypeError):
        FuncEnvelope(fun)
