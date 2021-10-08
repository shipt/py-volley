from abc import abstractmethod
from pprint import pprint
import time
import os

from rsmq import RedisSMQ

from typing import Any

from pyshipt_logging.logger import ShiptLogging


logger = ShiptLogging.get_default_logger()


class Component:

    def __init__(self, qname: str, host: str=None) -> None:
        # TODO: needs to be able to hand two queues, input and output
        self.host = host
        if self.host is None:
            self.host = os.environ["REDIS_HOST"]
        self.qname = qname
        self.queue = RedisSMQ(host=self.host, qname=qname)
        # TODO: is this "create if not exists. will this cause problems?"
        # TODO: vt probably should be configurable
        self.queue.createQueue(delay=0).vt(30).exceptions(False).execute()

    
    def publish(self, msg: dict[str, Any]) -> str:
        # TODO: this should publish to either kafka or redis
        msg_id: str = self.queue\
                .sendMessage()\
                .message(msg)\
                .execute()
        return msg_id

    def consume(self, poll_interval: float=1) -> dict[str, Any]:
        """pull a message off the queue"""
        # TODO: this should pull from either kafka or redis
        msg = None
        while not isinstance(msg, dict):
            msg: dict[str, Any] = self.queue\
                    .receiveMessage()\
                    .exceptions(False)\
                    .execute()
            if not isinstance(msg, dict):
                time.sleep(poll_interval)
        return msg

    def delete_msg(self, msg: dict[str, Any]) -> None:
        self.queue.deleteMessage(id=msg['id'])

    @abstractmethod
    def process(self) -> None:
        raise NotImplementedError
