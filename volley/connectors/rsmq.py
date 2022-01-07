import os
import time
from dataclasses import dataclass
from typing import Optional, Union

from prometheus_client import Summary
from rsmq import RedisSMQ

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger

QUIET = bool(os.getenv("DEBUG", True))

PROCESS_TIME = Summary("redis_process_time_seconds", "Time spent interacting with rsmq", ["operation"])


class RSMQConfigError(Exception):
    """problems with RSMQ config"""


@dataclass
class RSMQConsumer(BaseConsumer):
    # https://github.com/mlasevich/PyRSMQ#quick-intro-to-rsmq
    def __post_init__(self) -> None:
        if "host" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("REDIS_HOST"):
            self.config["host"] = host
        else:
            raise RSMQConfigError("RSMQ host not found in environment nor config")

        if "options" in self.config:
            if "decode_responses" in self.config["options"]:
                # if client is providing their own value, use it
                pass
            else:
                # otherwise set it to False. Serialization is handled elsewhere
                self.config["options"]["decode_responses"] = False
        else:
            # if no options provided, then provide these default options
            self.config["options"] = {"decode_responses": False}

        defaults = {"qname": self.queue_name, "exceptions": False, "vt": 60, "quiet": QUIET}

        defaults.update(self.config)
        self.config = defaults
        logger.info("RSMQ Consumer configs %s", self.config)
        self.queue = RedisSMQ(**self.config)
        self.queue.createQueue().execute()

    def consume(self, queue_name: str) -> Optional[QueueMessage]:
        """Polls RSMQ for a single message.

        Args:
            queue_name (str): name of queue to poll.

        Returns:
            Optional[QueueMessage]: The message and it's RSMQ.
        """
        _start = time.time()
        msg = self.queue.receiveMessage(qname=queue_name).exceptions(False).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        if isinstance(msg, dict):
            return QueueMessage(message_context=msg["id"], message=msg["message"])
        else:
            return None

    def delete_message(self, queue_name: str, message_context: str) -> bool:
        _start = time.time()
        result: bool = self.queue.deleteMessage(qname=queue_name, id=message_context).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("delete").observe(_duration)
        return result

    def on_fail(self) -> None:
        """no action on fail
        consumed message becomes available again once visibility timeout (vt) expires
        """
        pass

    def shutdown(self) -> None:
        self.queue.quit()


@dataclass
class RSMQProducer(BaseProducer):
    def __post_init__(self) -> None:
        if "host" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("REDIS_HOST"):
            self.config["host"] = host
        else:
            raise RSMQConfigError("RSMQ host not found in environment nor config")

        defaults = {"qname": self.queue_name, "delay": 0, "exceptions": False}

        defaults.update(self.config)
        self.config = defaults
        logger.info("RSMQ Producer configs: %s", self.config)
        self.queue = RedisSMQ(**self.config)
        self.queue.createQueue().execute()

    def produce(self, queue_name: str, message: bytes, **kwargs: Union[str, int]) -> bool:
        m = message
        _start = time.time()
        msg_id: str = self.queue.sendMessage(
            qname=queue_name,
            message=m,
            encode=kwargs.get("encode", False),
            delay=kwargs.get("delay", None),
            quiet=kwargs.get("quiet", False),
        ).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("write").observe(_duration)
        return bool(msg_id)

    def shutdown(self) -> None:
        self.queue.quit()
