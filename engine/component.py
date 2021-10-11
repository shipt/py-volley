
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Union
from engine.data_models import BundleMessage

from functools import wraps

def bundle_engine(input_type, output_type):

    def decorator(func):
        @wraps(func)
        def run_component(*args, **kwargs):
            if input_type == "kafka":
                from engine.kafka import BundleConsumer
                consumer = BundleConsumer(
                    host=os.environ["KAFKA_BROKERS"],
                    queue_name=os.environ["INPUT_QUEUE"],
                )
            elif input_type == "rsmq":
                from engine.rsmq import BundleConsumer
                consumer = BundleConsumer(
                    host=os.environ["REDIS_HOST"],
                    queue_name=os.environ["INPUT_QUEUE"],
                )
            else:
                raise NotImplementedError(f"{input_type=} not valid")

            if output_type == "kafka":
                from engine.kafka import BundleProducer
                producer = BundleProducer(
                    host=os.environ["KAFKA_BROKERS"],
                    queue_name=os.environ["OUTPUT_QUEUE"]
                )
            elif output_type == "rsmq":
                from engine.rsmq import BundleProducer
                producer = BundleProducer(
                    host=os.environ["REDIS_HOST"],
                    queue_name=os.environ["OUTPUT_QUEUE"]
                )
            else:
                raise NotImplementedError(f"{output_type=} not valid")

            while True:
                in_message: BundleMessage = consumer.consume(queue_name=os.environ["INPUT_QUEUE"])

                # TODO: func should return a tuple of out_message, output_queue (so we can recycle messages)     
                out_message: BundleMessage = func(in_message)

                status = producer.produce(
                    queue_name=os.environ["OUTPUT_QUEUE"],
                    message=out_message.dict()
                )

                if status:
                    consumer.delete_message(
                        queue_name=os.environ["INPUT_QUEUE"],
                        message_id=in_message.message_id
                    )
        return run_component
    return decorator
