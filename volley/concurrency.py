import asyncio
import contextvars
import functools
from typing import Any, Awaitable, Callable

from prometheus_client import Counter

from volley.util import FuncEnvelope

APP_STATUS = Counter("volley_app_completions", "Application cycle status", ["app_name", "status"])  # success/failure


async def run_in_threadpool(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_event_loop()
    child = functools.partial(func, *args)
    context = contextvars.copy_context()
    func = context.run
    args = (child,)
    return await loop.run_in_executor(None, func, *args)


async def run_worker_function(
    f: FuncEnvelope,
    message: Any,
    ctx: Any,
    app_name: str = "volley",
) -> Any:
    if f.needs_msg_ctx:
        f.func = functools.partial(f.func, **{f.message_ctx_param: ctx})
    try:
        if f.is_coroutine:
            fun_result = await f.func(message)
        else:
            fun_result = await run_in_threadpool(f.func, message)
    except Exception:
        APP_STATUS.labels(app_name=app_name, status="failure").inc()
        raise
    APP_STATUS.labels(app_name=app_name, status="success").inc()
    return fun_result


def run_async(func: Callable[..., Awaitable[Any]]) -> Callable[..., None]:
    def wrapper() -> None:
        asyncio.run(func())

    return wrapper
