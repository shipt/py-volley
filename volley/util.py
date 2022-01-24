import signal
from typing import Any

from volley.logging import logger


class GracefulKiller:
    def __init__(self) -> None:
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum: int, frame: Any) -> None:  # pylint: disable=W0613
        logger.warning("Received kill: %s", signum)
        self.kill_now = True
