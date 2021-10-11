from dataclasses import dataclass
import json
import time
from typing import Any, Dict

from rsmq import RedisSMQ

from engine.data_models import BundleMessage
from engine.consumer import Consumer
from engine.producer import Producer



@dataclass
class BundleConsumer(Consumer):

    def __post_init__(self) -> None:
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name)
        # TODO: visibility timeout (vt) probably be configurable
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

    def consume(self, queue_name: str, timeout: float=30.0, poll_interval: float=0.25) -> BundleMessage:
        msg = None
        while not isinstance(msg, dict):
            msg = self.queue\
                    .receiveMessage(qname=queue_name, vt=timeout)\
                    .exceptions(False)\
                    .execute()
            
            if isinstance(msg, dict):
                return BundleMessage(
                    message_id=msg["id"],
                    params={},
                    message=json.loads(msg["message"])
                )
            else:
                time.sleep(poll_interval)
    
    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        result = self.queue.deleteMessage(qname=queue_name, id=message_id).execute()
        return True


@dataclass
class BundleProducer(Producer):

    def __post_init__(self) -> None:
        self.queue = RedisSMQ(host=self.host, qname=self.queue_name)
        self.queue.createQueue(delay=0).vt(60).exceptions(False).execute()

    def produce(self, queue_name: str, message: Dict[str, Any]) -> bool:
        msg_id: str = self.queue\
            .sendMessage(
                qname=queue_name,
                message=message["message"]
            )\
            .execute()
        return bool(msg_id)
