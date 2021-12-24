from uuid import uuid4

import pytest

from volley.concurrency import run_worker_function


@pytest.mark.asyncio
async def test_run_worker_function() -> None:
    async_msg = str(uuid4())
    sync_msg = str(uuid4())

    async def async_fun(msg: str) -> str:
        return msg

    def sync_fun(msg: str) -> str:
        return msg

    async_res = await run_worker_function(async_fun, message=async_msg, is_coroutine=True)
    assert async_res == async_msg
    sync_res = await run_worker_function(sync_fun, message=sync_msg, is_coroutine=False)
    assert sync_res == sync_msg
