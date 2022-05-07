import asyncio
import inspect
import signal
from dataclasses import dataclass, field
from typing import Any, Callable

from volley.logging import logger


class GracefulKiller:
    def __init__(self) -> None:
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum: int, frame: Any) -> None:  # pylint: disable=W0613
        logger.warning("Received kill: %s", signum)
        self.kill_now = True


@dataclass
class FuncEnvelope:
    func: Callable[..., Any]

    message_ctx_param: str = "msg_ctx"

    needs_msg_ctx: bool = field(init=False)
    is_coroutine: bool = field(init=False)
    message_param: str = field(init=False)

    def __post_init__(self) -> None:
        self.is_coroutine = asyncio.iscoroutinefunction(self.func)
        func_params = dict(inspect.signature(self.func).parameters)

        # validate parameters
        num_param_expected = 1
        self.needs_msg_ctx = self.message_ctx_param in func_params
        if self.needs_msg_ctx:
            num_param_expected = 2
            remaining_params = {k: v for k, v in func_params.items() if k != self.message_ctx_param}
        else:
            remaining_params = func_params
        # remaining param is name of the user provided message param
        if len(remaining_params) != 1:
            raise TypeError(
                f"Function '{self.func.__name__}' has too many arguments."
                f"Expected {num_param_expected}. Provided {func_params.keys()}"
            )

        # TODO: validation type annotation on message_param agrees with queue config
        self.message_param = list(remaining_params.keys())[0]
