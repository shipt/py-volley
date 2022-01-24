import signal
from typing import Any


class GracefulKiller:
    def __init__(self) -> None:
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum: int, frame: Any) -> None:  # pylint: disable=W0613
        self.kill_now = True
