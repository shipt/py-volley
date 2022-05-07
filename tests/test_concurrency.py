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
