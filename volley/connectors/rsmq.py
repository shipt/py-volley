import json
import os
import time
from dataclasses import dataclass

from prometheus_client import Summary
from rsmq import RedisSMQ

from engine.connectors.base import Consumer, Producer
from engine.data_models import QueueMessage
from engine.logging import logger

QUIET = bool(os.getenv("DEBUG", True))

PROCESS_TIME = Summary("redis_process_time_seconds", "Time spent interacting with rsmq", ["operation"])


@dataclass
class RSMQConsumer(Consumer):
    def __post_init__(self) -> None:
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name)
        # TODO: visibility timeout (vt) probably be configurable
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

    def consume(self, queue_name: str, timeout: float = 30.0, poll_interval: float = 1) -> QueueMessage:
        msg = None
        while not isinstance(msg, dict):
            _start = time.time()
            msg = self.queue.receiveMessage(qname=queue_name, vt=timeout, quiet=QUIET).exceptions(False).execute()
            _duration = time.time() - _start
            PROCESS_TIME.labels("read").observe(_duration)
            if isinstance(msg, dict):
                return QueueMessage(message_id=msg["id"], message=json.loads(msg["message"]))
            else:
                time.sleep(poll_interval)

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
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name)
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        m = message.dict()["message"]
        logger.info(f"queue_name - {queue_name}")
        msg = json.dumps(m, default=str)
        _start = time.time()
        msg_id: str = self.queue.sendMessage(qname=queue_name, message=msg, encode=True).execute()
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        return bool(msg_id)

    def shutdown(self) -> None:
        self.queue.quit()
