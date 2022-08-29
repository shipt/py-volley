from uuid import uuid4

import pytest

from volley.concurrency import run_worker_function
from volley.util import FuncEnvelope


@pytest.mark.asyncio
async def test_run_worker_function() -> None:
    async_msg = str(uuid4())
    sync_msg = str(uuid4())

    async def async_fun(msg: str) -> str:
        return msg

    def sync_fun(msg: str) -> str:
        return msg

    wrapped_async = FuncEnvelope(async_fun)
    wrapped_sync = FuncEnvelope(sync_fun)

    async_res = await run_worker_function(wrapped_async, message=async_msg, ctx="test-context")
    assert async_res == async_msg
    sync_res = await run_worker_function(wrapped_sync, message=sync_msg, ctx="test-context")
    assert sync_res == sync_msg


@pytest.mark.asyncio
async def test_run_worker_function_fail() -> None:
    """unhandled app exceptions should crash hard"""

    async def async_fun(msg: str) -> str:
        raise Exception()

    def sync_fun(msg: str) -> str:
        raise Exception()

    wrapped_async = FuncEnvelope(async_fun)
    wrapped_sync = FuncEnvelope(sync_fun)

    with pytest.raises(Exception):
        await run_worker_function(wrapped_async, message="msg", ctx="test-context")
    with pytest.raises(Exception):
        await run_worker_function(wrapped_sync, message="msg", ctx="test-context")
