import importlib
import os
from functools import wraps
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from core.logging import logger
from engine.connectors.base import Consumer, Producer
from engine.data_models import ComponentMessage, QueueMessage
from engine.queues import Queue, Queues, available_queues

# enables mocking the infinite loop to finite
RUN_ONCE = False


def get_consumer(queue_type: str, queue_name: str) -> Consumer:
    if queue_type == "kafka":
        from engine.connectors import KafkaConsumer

        return KafkaConsumer(
            host=os.environ["KAFKA_BROKERS"],
            queue_name=queue_name,
        )
    elif queue_type == "rsmq":
        from engine.connectors import RSMQConsumer

        return RSMQConsumer(
            host=os.environ["REDIS_HOST"],
            queue_name=queue_name,
        )
    elif queue_type == "postgres":
        from engine.connectors import PGConsumer

        return PGConsumer(
            host=os.getenv("PG_HOST", "postgres"),
            queue_name=queue_name,
        )
    else:
        raise KeyError(f"{queue_type=} not valid")


def get_producer(queue_type: str, queue_name: str) -> Producer:
    if queue_type == "kafka":
        from engine.connectors import KafkaProducer

        return KafkaProducer(host=os.environ["KAFKA_BROKERS"], queue_name=queue_name)

    elif queue_type == "rsmq":
        from engine.connectors import RSMQProducer

        return RSMQProducer(host=os.environ["REDIS_HOST"], queue_name=queue_name)

    elif queue_type == "postgres":
        from engine.connectors import PGProducer

        return PGProducer(host=os.getenv("PG_HOST", "postgres"), queue_name=queue_name)

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
    out_queues["dead-letter-queue"] = queues.queues["dead-letter-queue"]

    def decorator(func):  # type: ignore
        @wraps(func)
        def run_component(*args, **kwargs) -> None:  # type: ignore
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked
            in_queue.q = get_consumer(queue_type=in_queue.type, queue_name=in_queue.value)

            input_data_class: ComponentMessage = load_schema_class(in_queue)

            for qname, q in out_queues.items():
                q.q = get_producer(queue_name=q.value, queue_type=q.type)

            # queue connections were setup above. now we can start to interact with the queues
            while True:

                # read message off the specified queue
                in_message: QueueMessage = in_queue.q.consume(queue_name=in_queue.value)

                outputs: List[Tuple[str, ComponentMessage]] = []
                # every queue has a schema - validate the data coming off the queue
                # generally, data is validate before it goes on to a queue
                # however, if a service outside bundle_engine is publishing to the queue,
                # validation may not be guaranteed
                # example - input_topic - anyone at Shipt can publish to it
                try:
                    serialized_message: ComponentMessage = input_data_class.parse_obj(in_message.message)
                except ValidationError:
                    logger.exception(
                        f"""
                        Error validating message from {in_queue.value}"""
                    )
                    outputs = [("dead-letter-queue", ComponentMessage.parse_obj(in_message.message))]

                if not outputs:
                    outputs = func(serialized_message)

                for qname, component_msg in outputs:
                    if component_msg is None:
                        continue
                    q_msg = QueueMessage(message_id="", message=component_msg.dict())

                    try:
                        out_queue = out_queues[qname]
                    except KeyError:
                        logger.exception(f"{qname} is not defined in this component's output queue list")

                    # typing of engine.queues.Queue.q makes this ambiguous and potentially error prone
                    try:
                        status = out_queue.q.produce(queue_name=out_queue.value, message=q_msg)  # type: ignore
                    except Exception:
                        logger.exception("failed producing message")
                        status = False
                    if status:
                        in_queue.q.delete_message(
                            queue_name=in_queue.value,
                            message_id=in_message.message_id,
                        )
                    else:
                        in_queue.q.on_fail()

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

        run_component.__wrapped__ = func  # type: ignore  # used for unit testing
        return run_component

    return decorator
