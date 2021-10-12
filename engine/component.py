
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Union, List
from engine.data_models import BundleMessage

from engine.queues import Queue, Queues, available_queues

from functools import wraps

def bundle_engine(input_queue: str, output_queues: List[str]):
    queues: Queues = available_queues()

    in_queue: Queue = queues.queues[input_queue]

    out_queues: Dict[str, Queue] = {x: queues.queues[x] for x in output_queues}

    def decorator(func):
        @wraps(func)
        def run_component(*args, **kwargs):
            if in_queue.type == "kafka":
                from engine.kafka import BundleConsumer
                in_queue.q = BundleConsumer(
                    host=os.environ["KAFKA_BROKERS"],
                    queue_name=in_queue.value,
                )
            elif in_queue.type == "rsmq":
                from engine.rsmq import BundleConsumer
                in_queue.q = BundleConsumer(
                    host=os.environ["REDIS_HOST"],
                    queue_name=in_queue.value,
                )
            else:
                raise NotImplementedError(f"{in_queue.type=} not valid")

            for qname, q in out_queues.items():
                if q.type == "kafka":
                    from engine.kafka import BundleProducer
                    q.q = BundleProducer(
                        host=os.environ["KAFKA_BROKERS"],
                        queue_name=q.value
                    )
                elif q.type == "rsmq":
                    from engine.rsmq import BundleProducer
                    q.q = BundleProducer(
                        host=os.environ["REDIS_HOST"],
                        queue_name=q.value
                    )
                else:
                    raise NotImplementedError(f"{q.q=} not valid")

            while True:
                in_message: BundleMessage = in_queue.q.consume(queue_name=in_queue.value)

                # TODO: func should return a tuple of out_message, output_queue (so we can recycle messages)     
                out_message, next_queue = func(in_message)

                out_queue = out_queues[next_queue]

                status = out_queue.q.produce(
                    queue_name=out_queues[next_queue].value,
                    message=out_message.dict()
                )

                if status:
                    in_queue.q.delete_message(
                        queue_name=in_queue.value,
                        message_id=in_message.message_id
                    )
        return run_component
    return decorator
