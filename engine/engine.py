import importlib
import os
from functools import wraps
from typing import Any, Dict, List, Tuple

from pydantic.main import BaseModel

from core.logging import logger
from engine.consumer import Consumer
from engine.data_models import QueueMessage
from engine.producer import Producer
from engine.queues import Queue, Queues, available_queues

# enables mocking the infinite loop to finite
RUN = True


def get_consumer(queue_type: str, queue_name: str) -> Consumer:
    if queue_type == "kafka":
        from engine.kafka import BundleConsumer

        return BundleConsumer(
            host=os.environ["KAFKA_BROKERS"],
            queue_name=queue_name,
        )
    elif queue_type == "rsmq":
        from engine.rsmq import BundleConsumer  # type: ignore

        return BundleConsumer(
            host=os.environ["REDIS_HOST"],
            queue_name=queue_name,
        )
    elif queue_type == "postgres":
        from engine.stateful.postgres import PGConsumer

        return PGConsumer(  # type: ignore
            host=os.getenv("PG_HOST", "postgres"),
            queue_name=queue_name,
        )
    else:
        raise KeyError(f"{queue_type=} not valid")


def get_producer(queue_type: str, queue_name: str) -> Producer:
    if queue_type == "kafka":
        from engine.kafka import BundleProducer

        return BundleProducer(host=os.environ["KAFKA_BROKERS"], queue_name=queue_name)

    elif queue_type == "rsmq":
        from engine.rsmq import BundleProducer as RsmqProducer

        return RsmqProducer(host=os.environ["REDIS_HOST"], queue_name=queue_name)

    elif queue_type == "postgres":
        from engine.stateful.postgres import PGProducer

        return PGProducer(host=os.getenv("PG_HOST", "postgres"), queue_name=queue_name)  # type: ignore

    else:
        raise KeyError(f"{queue_type=} not valid")


def load_schema_class(q: Queue) -> Any:
    if q.model_schema in ["dict"]:
        return dict
    else:
        modules = q.model_schema.split(".")
        class_obj = modules[-1]
        pathmodule = ".".join(modules[:-1])
        module = importlib.import_module(pathmodule)
        return getattr(module, class_obj)


def bundle_engine(input_queue: str, output_queues: List[str]) -> Any:  # noqa: C901
    queues: Queues = available_queues()

    in_queue: Queue = queues.queues[input_queue]

    out_queues: Dict[str, Queue] = {x: queues.queues[x] for x in output_queues}

    def decorator(func):  # type: ignore
        @wraps(func)
        def run_component(*args, **kwargs) -> None:  # type: ignore
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked
            in_queue.q = get_consumer(
                queue_type=in_queue.type, queue_name=in_queue.value
            )

            input_data_class: Any = load_schema_class(in_queue)

            for qname, q in out_queues.items():
                q.q = get_producer(queue_name=q.value, queue_type=q.type)

            # queue connections were setup above. now we can start to interact with the queues
            while RUN:

                in_message: QueueMessage = in_queue.q.consume(queue_name=in_queue.value)

                # convert in_message.message to the appropriate data model
                if isinstance(input_data_class, dict):
                    # if there's no schema, do nothing. leave the message as a dict
                    continue
                else:
                    # otherwise serialize to the components data model
                    in_message.message = input_data_class(**in_message.message)

                outputs: List[Tuple[str, QueueMessage]] = func(in_message.message)

                for qname, m in outputs:
                    m = QueueMessage(message_id="", message=m.dict())

                    try:
                        out_queue = out_queues[qname]
                    except KeyError:
                        logger.exception(
                            f"{qname} is not defined in this component's output queue list"
                        )

                    # typing of engine.queues.Queue.q makes this ambiguous and potentially error prone
                    try:
                        status = out_queue.q.produce(queue_name=out_queue.value, message=m)  # type: ignore
                    except Exception:
                        logger.exception("failed producing message")
                        status = False
                    if status:
                        in_queue.q.delete_message(
                            queue_name=in_queue.value, message_id=in_message.message_id
                        )
                    else:
                        in_queue.q.on_fail()

        run_component.__wrapped__ = func  # type: ignore  # used for unit testing
        return run_component

    return decorator
