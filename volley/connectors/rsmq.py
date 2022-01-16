import os
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

from prometheus_client import Summary
from rsmq import RedisSMQ
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger

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

        defaults = {"qname": self.queue_name, "exceptions": True, "vt": 60}

        defaults.update(self.config)
        self.config = defaults
        logger.info("RSMQ Consumer configs %s", self.config)
        self.queue = RedisSMQ(**self.config)
        logger.info("Creatng queue: %s", self.queue_name)
        self.queue.createQueue().exceptions(False).execute()

    def consume(self, queue_name: str) -> Optional[QueueMessage]:
        """Polls RSMQ for a single message.

        Args:
            queue_name (str): name of queue to poll.

        Returns:
            Optional[QueueMessage]: The message and it's RSMQ.
        """
        _start = time.time()
        msg = self.queue.receiveMessage(qname=queue_name, quiet=True).exceptions(False).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        if isinstance(msg, dict):
            return QueueMessage(message_context=msg["id"], message=msg["message"])
        else:
            return None

    def on_success(self, queue_name: str, message_context: str) -> bool:
        _start = time.time()
        result: bool = self.delete_message(queue_name=queue_name, message_context=message_context)
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        return result

    def on_fail(self, queue_name: str, message_context: str) -> None:
        """message will become visible once visbility timeout expires"""
        # self.queue.changeMessageVisibility(qname=queue_name, id=message_context, vt=0)
        logger.error(
            "Failed producing message id %s." "Message will reappear in queue `%s` when timeout expires",
            message_context,
            queue_name,
        )

    def shutdown(self) -> None:
        self.queue.quit()

    @retry(reraise=True, wait=wait_exponential(multiplier=1, min=4, max=10))
    def delete_message(self, queue_name: str, message_context: str) -> bool:
        """wrapper function to handle retries
        retrying forever with exponential backoff
        """
        result: bool = self.queue.deleteMessage(qname=queue_name, id=message_context).execute()
        if result:
            return result
        else:
            raise TimeoutError(f"Failed deleting message: '{message_context}' from queue: '{queue_name}'")


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

        defaults = {"qname": self.queue_name, "delay": 0, "exceptions": True}

        defaults.update(self.config)
        self.config = defaults
        logger.info("RSMQ Producer configs: %s", self.config)
        self.queue = RedisSMQ(**self.config)
        logger.info("Creatng queue: %s", self.queue_name)
        self.queue.createQueue().exceptions(False).execute()

    def produce(self, queue_name: str, message: bytes, **kwargs: Union[str, int]) -> bool:
        _start = time.time()
        status: bool = self.send_message(queue_name=queue_name, message=message, produce_cfg=kwargs)
        _duration = time.time() - _start
        PROCESS_TIME.labels("write").observe(_duration)
        return status

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_fixed(2))
    def send_message(self, queue_name: str, message: bytes, produce_cfg: dict[str, Any]) -> bool:
        """wrapper function to handle retries retrying"""
        msg_id: str = self.queue.sendMessage(
            qname=queue_name,
            message=message,
            encode=produce_cfg.get("encode", False),
            delay=produce_cfg.get("delay", None),
            quiet=produce_cfg.get("quiet", False),
        ).execute()
        return bool(msg_id)

    def shutdown(self) -> None:
        self.queue.quit()
