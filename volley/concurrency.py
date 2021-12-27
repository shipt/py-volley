import asyncio
import contextvars
import functools
from typing import Any, Awaitable, Callable


async def run_in_threadpool(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_event_loop()
    child = functools.partial(func, *args)
    context = contextvars.copy_context()
    func = context.run
    args = (child,)
    return await loop.run_in_executor(None, func, *args)


async def run_worker_function(func: Any, message: Any, is_coroutine: bool) -> Any:
    if is_coroutine:
        return await func(message)
    else:
        return await run_in_threadpool(func, message)


def run_async(func: Callable[..., Awaitable[Any]]) -> Callable[..., None]:
    def wrapper() -> None:
        asyncio.run(func())

    return wrapper
