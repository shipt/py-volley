import os
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

import zmq
from prometheus_client import Summary

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger

PROCESS_TIME = Summary("zmq_process_time_seconds", "Time spent interacting with zmq", ["operation"])

context = zmq.Context()
_socket = None


def init_zmq(port: int) -> None:
    global context
    global _socket
    if _socket is None:
        _socket = context.socket(zmq.REP)
        _socket.bind("tcp://*:%s" % port)
    else:
        logger.info("Socket already initialized")


@dataclass
class ZMQConsumer(BaseConsumer):
    def __post_init__(self) -> None:
        if "host" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("ZMQ_HOST"):
            self.config["host"] = host
        if "port" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("ZMQ_PORT"):
            self.config["port"] = host
        init_zmq(port=self.config["port"])

    def consume(self) -> Optional[QueueMessage]:
        global _socket
        _start = time.time()
        msg = _socket.recv()
        _duration = time.time() - _start
        PROCESS_TIME.labels("read").observe(_duration)
        if msg:
            return QueueMessage(message_context=None, message=msg)
        else:
            return None

    def on_success(self, message_context: str) -> None:
        pass

    def on_fail(self, message_context: str) -> None:
        pass

    def shutdown(self) -> None:
        global _socket
        global _socket
        _socket.close()
        context.term()


@dataclass
class ZMQProducer(BaseProducer):
    def __post_init__(self) -> None:
        # delivery reports are synchronous
        self.callback_delivery = False
        if "host" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("ZMQ_HOST"):
            self.config["host"] = host
        if "port" in self.config:
            # pass the value directly to the constructor
            pass
        elif host := os.getenv("ZMQ_PORT"):
            self.config["port"] = host
        init_zmq(port=self.config["port"])

    def produce(
        self, queue_name: str, message: bytes, message_context: Optional[Any] = None, **kwargs: Union[str, int]
    ) -> bool:
        global _socket
        _start = time.time()
        _socket.send(message)
        _duration = time.time() - _start
        PROCESS_TIME.labels("write").observe(_duration)
        return True

    def shutdown(self) -> None:
        global _socket
        global _socket
        _socket.close()
        context.term()
