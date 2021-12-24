import asyncio
import contextvars
import functools
import typing
from typing import Any, Callable

import anyio


async def run_in_threadpool(func: typing.Callable[..., Any], *args: typing.Any) -> Any:
    # Ensure we run in the same context
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


def run_async(func: Callable[..., Any]) -> Callable[..., None]:
    def wrapper() -> None:
        asyncio.run(func())

    return wrapper
