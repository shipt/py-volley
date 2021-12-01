import os
import time
from dataclasses import dataclass
from typing import Optional

from prometheus_client import Summary
from rsmq import RedisSMQ

from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage
from volley.logging import logger

QUIET = bool(os.getenv("DEBUG", True))

PROCESS_TIME = Summary("redis_process_time_seconds", "Time spent interacting with rsmq", ["operation"])


class RSMQConfigError(Exception):
    """problems with RSMQ config"""


@dataclass
class RSMQConsumer(Consumer):
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

        defaults = {"qname": self.queue_name, "exceptions": False, "vt": 60}

        defaults.update(self.config)
        self.config = defaults
        logger.info(f"RSMQ Consumer configs: {self.config}")
        self.queue = RedisSMQ(**self.config)
        self.queue.createQueue().execute()

    def consume(self, queue_name: str, timeout: float = 30.0, poll_interval: float = 1) -> Optional[QueueMessage]:
        """Polls RSMQ for a single message.

        Args:
            queue_name (str): name of queue to poll.
            timeout (float, optional): alias for RSMQ visibility_timeout Defaults to 30.0.
            poll_interval (float, optional): Defaults to 1.

        Returns:
            Optional[QueueMessage]: The message and it's RSMQ.
        """
        _start = time.time()
        msg = self.queue.receiveMessage(qname=queue_name, vt=timeout, quiet=QUIET).exceptions(False).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        if isinstance(msg, dict):
            return QueueMessage(message_id=msg["id"], message=msg["message"])
        else:
            return None

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        _start = time.time()
        result: bool = self.queue.deleteMessage(qname=queue_name, id=message_id).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("delete").observe(_duration)
        return result

    def on_fail(self) -> None:
        pass

    def shutdown(self) -> None:
        self.queue.quit()


@dataclass
class RSMQProducer(Producer):
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
        logger.info(f"RSMQ Producer configs: {self.config}")
        self.queue = RedisSMQ(**self.config)
        self.queue.createQueue().execute()

    def produce(self, queue_name: str, message: bytes) -> bool:
        m = message
        logger.info(f"queue_name - {queue_name}")
        _start = time.time()
        msg_id: str = self.queue.sendMessage(qname=queue_name, message=m, encode=False).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("write").observe(_duration)
        return bool(msg_id)

    def shutdown(self) -> None:
        self.queue.quit()
