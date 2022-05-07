import asyncio
import contextvars
import functools
from typing import Any, Awaitable, Callable

from volley.util import FuncEnvelope


async def run_in_threadpool(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_event_loop()
    child = functools.partial(func, *args)
    context = contextvars.copy_context()
    func = context.run
    args = (child,)
    return await loop.run_in_executor(None, func, *args)


async def run_worker_function(f: FuncEnvelope, message: Any, ctx: Any) -> Any:
    if f.needs_msg_ctx:
        f.func = functools.partial(f.func, **{f.message_ctx_param: ctx})
    if f.is_coroutine:
        return await f.func(message)
    else:
        return await run_in_threadpool(f.func, message)


def run_async(func: Callable[..., Awaitable[Any]]) -> Callable[..., None]:
    def wrapper() -> None:
        asyncio.run(func())

    return wrapper
