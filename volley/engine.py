import importlib
import os
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Tuple

from prometheus_client import Counter, Summary, start_http_server
from pydantic import ValidationError

from volley.config import METRICS_ENABLED, METRICS_PORT
from volley.connectors.base import Consumer, Producer
from volley.data_models import ComponentMessage, QueueMessage
from volley.logging import logger
from volley.queues import Queue, Queues, available_queues

# enables mocking the infinite loop to finite
RUN_ONCE = False


PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["process_name"])
MESSAGE_CONSUMED = Counter("messages_consumed_count", "Messages consumed from input", ["status"])  # success or fail
MESSAGES_PRODUCED = Counter("messages_produced_count", "Messages produced to output destination(s)", ["destination"])


def get_consumer(queue_type: str, queue_name: str) -> Consumer:
    if queue_type == "kafka":
        from volley.connectors import KafkaConsumer

        return KafkaConsumer(
            host=os.environ["KAFKA_BROKERS"],
            queue_name=queue_name,
        )
    elif queue_type == "rsmq":
        from volley.connectors import RSMQConsumer

        return RSMQConsumer(
            host=os.environ["REDIS_HOST"],
            queue_name=queue_name,
        )
    elif queue_type == "postgres":
        from volley.connectors import PGConsumer

        return PGConsumer(
            host=os.getenv("PG_HOST", "postgres"),
            queue_name=queue_name,
        )
    else:
        raise KeyError(f"{queue_type=} not valid")


def get_producer(queue_type: str, queue_name: str) -> Producer:
    if queue_type == "kafka":
        from volley.connectors import KafkaProducer

        return KafkaProducer(host=os.environ["KAFKA_BROKERS"], queue_name=queue_name)

    elif queue_type == "rsmq":
        from volley.connectors import RSMQProducer

        return RSMQProducer(host=os.environ["REDIS_HOST"], queue_name=queue_name)

    elif queue_type == "postgres":
        from volley.connectors import PGProducer

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


@dataclass
class Engine:
    """initializes configuration for input and output workers"""

    input_queue: str
    output_queues: List[str]

    def __post_init__(self) -> None:

        self.queues: Queues = available_queues()

        self.in_queue: Queue = self.queues.queues[self.input_queue].copy()

        self.out_queues: Dict[str, Queue] = {x: self.queues.queues[x] for x in self.output_queues}
        self.out_queues["dead-letter-queue"] = self.queues.queues["dead-letter-queue"]

    def stream_app(  # noqa: C901
        self, func: Callable[[ComponentMessage], List[Tuple[str, ComponentMessage]]]
    ) -> Callable[..., Any]:
        @wraps(func)
        def run_component(*args, **kwargs) -> None:  # type: ignore
            if METRICS_ENABLED:
                start_http_server(port=METRICS_PORT)
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked
            self.in_queue.qcon = get_consumer(queue_type=self.in_queue.type, queue_name=self.in_queue.value)

            input_data_class: ComponentMessage = load_schema_class(self.in_queue)

            for qname, q in self.out_queues.items():
                q.qcon = get_producer(queue_name=q.value, queue_type=q.type)

            # queue connections were setup above. now we can start to interact with the queues
            while True:
                _start_time = time.time()

                # read message off the specified queue
                in_message: QueueMessage = self.in_queue.qcon.consume(queue_name=self.in_queue.value)

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
                        Error validating message from {self.in_queue.value}"""
                    )
                    outputs = [("dead-letter-queue", ComponentMessage.parse_obj(in_message.message))]

                if not outputs:
                    _start_main = time.time()
                    outputs = func(serialized_message)
                    _fun_duration = time.time() - _start_main
                    PROCESS_TIME.labels("component").observe(_fun_duration)

                all_produce_status: List[bool] = []
                for qname, component_msg in outputs:
                    if component_msg is None:
                        continue
                    q_msg = QueueMessage(message_id="", message=component_msg.dict())

                    try:
                        out_queue = self.out_queues[qname]
                    except KeyError:
                        logger.exception(f"{qname} is not defined in this component's output queue list")

                    # TODO: typing of engine.queues.Queue.qcon makes this ambiguous and potentially error prone
                    try:
                        status = out_queue.qcon.produce(queue_name=out_queue.value, message=q_msg)  # type: ignore
                        MESSAGES_PRODUCED.labels(destination=qname).inc()
                    except Exception:
                        logger.exception("failed producing message")
                        status = False
                    all_produce_status.append(status)

                if all(all_produce_status):
                    # TODO - better handling of success criteria
                    # if multiple outputs - how to determine if its a success if one fails
                    self.in_queue.qcon.delete_message(
                        queue_name=self.in_queue.value,
                        message_id=in_message.message_id,
                    )
                    MESSAGE_CONSUMED.labels("success").inc()
                else:
                    self.in_queue.qcon.on_fail()
                    MESSAGE_CONSUMED.labels("fail").inc()
                _duration = time.time() - _start_time
                PROCESS_TIME.labels("cycle").observe(_duration)

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

        # used for unit testing as a means to access the wrapped component without the decorator
        run_component.__wrapped__ = func  # type: ignore
        return run_component
