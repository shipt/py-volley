
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
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked
            if in_queue.type == "kafka":
                from engine.kafka import BundleConsumer
                in_queue.q = BundleConsumer(
                    host=os.environ["KAFKA_BROKERS"],
                    queue_name=in_queue.value,
                )
            elif in_queue.type == "rsmq":
                from engine.rsmq import BundleConsumer  # type: ignore
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
                    from engine.rsmq import BundleProducer  # type: ignore
                    q.q = BundleProducer(
                        host=os.environ["REDIS_HOST"],
                        queue_name=q.value
                    )
                else:
                    raise NotImplementedError(f"{q.type=} not valid")

            # queue connections were setup above. now we can start to interact with the queues
            while True:
                
                in_message: BundleMessage = in_queue.q.consume(queue_name=in_queue.value)

                outputs: Dict[str, BundleMessage] = func(in_message)

                for qname, m in outputs.items():

                    out_queue = out_queues[qname]

                    status = out_queue.q.produce(
                        queue_name=out_queue.value,
                        message=m.dict()
                    )

                    if status:
                        in_queue.q.delete_message(
                            queue_name=in_queue.value,
                            message_id=in_message.message_id
                        )
        return run_component
    return decorator
