import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from prometheus_client import Summary
from rsmq import RedisSMQ
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage

logger = logging.getLogger(__name__)

PROCESS_TIME = Summary("redis_process_time_seconds", "Time spent interacting with rsmq", ["operation"])


class RSMQConfigError(Exception):
    """problems with RSMQ config"""


@dataclass
class RSMQConsumer(BaseConsumer):
    """Handles consuming messages from Redis Simple Message Queue
    [https://github.com/mlasevich/PyRSMQ#quick-intro-to-rsmq](https://github.com/mlasevich/PyRSMQ#quick-intro-to-rsmq)
    - pseudo example usage and configurations available on volley.Engine init:
    ```python hl_lines="4 6-12"
    from volley import Engine
    config = {
        "my_rsmq_queue": {
            "consumer": "volley.connectors.RSMQConsumer",
            "serializer": "volley.serializers.OrJsonSerialization",
            "config": {
                "host": "<hostname for the redis instance>",
                "port": "port for the redis instance, defaults to 6379",
                "vt": 120,
                "options": {
                    "decode_responses": False,
                }
            }
        }
    }
    app = Engine(
        input_queue="my_rsmq_queue",
        queue_config=config,
        ...
    )
    ```
    """

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
        self.queue = RedisSMQ(**self.config)
        logger.info("Creating queue: %s", self.queue_name)
        self.queue.createQueue().exceptions(False).execute()

    def consume(self) -> Optional[QueueMessage]:
        """Polls RSMQ for a single message.

            RSMQ consume returns a dictionary from the queue:
            # https://github.com/mlasevich/PyRSMQ/blob/master/README.md
            {
                message: Any - the message content
                rc: int - receive count - how many times this message was received
                ts: int - unix timestamp of when the message was originally sent
                id: str - message id
            }

        Returns:
            Optional[QueueMessage]: The message body and it's RSMQ object.
        """
        _start = time.time()
        msg = (
            self.queue.receiveMessage(qname=self.queue_name, quiet=True, vt=self.config["vt"])
            .exceptions(False)
            .execute()
        )
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        if isinstance(msg, dict):
            if isinstance(msg["id"], bytes):
                # message id is bytes when decode_response = False
                msg["id"] = msg["id"].decode("utf-8")
            return QueueMessage(message_context=msg["id"], message=msg["message"])
        else:
            return None

    def on_success(self, message_context: str) -> None:
        _start = time.time()
        self.delete_message(message_id=message_context)
        _duration = time.time() - _start
        PROCESS_TIME.labels("delete").observe(_duration)

    def on_fail(self, message_context: str) -> None:
        """message will become visible once visibility timeout expires"""
        # self.queue.changeMessageVisibility(qname=queue_name, id=message_context, vt=0)
        logger.error(
            "Failed producing message id %s." "Message will reappear in queue `%s` when timeout expires",
            message_context,
            self.queue_name,
        )

    def shutdown(self) -> None:
        self.queue.quit()

    @retry(reraise=True, stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=10))
    def delete_message(self, message_id: str) -> bool:
        """wrapper function to handle retries

        Raises a TimeoutError after attempts have been exhausted.
        """
        result: bool = self.queue.deleteMessage(qname=self.queue_name, id=message_id).execute()
        if result:
            return result
        else:
            err = f"Failed deleting message: '{message_id}' from queue: '{self.queue_name}'"
            logger.critical(err)
            raise TimeoutError(err)


@dataclass
class RSMQProducer(BaseProducer):
    def __post_init__(self) -> None:
        # delivery reports are synchronous
        self.callback_delivery = False

        if "host" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("REDIS_HOST"):
            self.config["host"] = host
        else:
            raise RSMQConfigError("RSMQ host not found in environment nor config")

        defaults = {
            "qname": self.queue_name,
            "delay": 0,
            "exceptions": True,
        }

        defaults.update(self.config)
        self.config = defaults
        self.queue = RedisSMQ(**self.config)
        logger.info("Creating queue: %s", self.queue_name)
        self.queue.createQueue().exceptions(False).execute()

    def produce(
        self, queue_name: str, message: bytes, message_context: Optional[Any] = None, **kwargs: Union[str, int]
    ) -> bool:
        _start = time.time()
        status: bool = self.send_message(queue_name=queue_name, message=message, produce_cfg=kwargs)
        _duration = time.time() - _start
        PROCESS_TIME.labels("write").observe(_duration)
        return status

    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_fixed(2))
    def send_message(self, queue_name: str, message: bytes, produce_cfg: Dict[str, Any]) -> bool:
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
