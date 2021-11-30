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


@dataclass
class RSMQConsumer(Consumer):
    def __post_init__(self) -> None:
        self.host = os.environ["REDIS_HOST"]
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name, options={"decode_responses": False})
        # TODO: visibility timeout (vt) probably be configurable
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

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
        self.host = os.environ["REDIS_HOST"]
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name)
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

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
