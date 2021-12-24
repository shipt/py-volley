import asyncio
import contextvars
import functools
from typing import Any, Awaitable, Callable

import anyio


async def run_in_threadpool(func: Callable[..., Any], *args: Any) -> Any:
    child = functools.partial(func, *args)
    context = contextvars.copy_context()
    func = context.run
    args = (child,)
    return await anyio.to_thread.run_sync(func, *args)


async def run_worker_function(func: Any, message: Any, is_coroutine: bool) -> Any:
    if is_coroutine:
        return await func(message)
    else:
        return await run_in_threadpool(func, message)


def run_async(func: Callable[..., Awaitable[Any]]) -> Callable[..., None]:
    def wrapper() -> None:
        asyncio.run(func())

    return wrapper
