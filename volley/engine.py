import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from prometheus_client import Counter, Summary, start_http_server
from pydantic import ValidationError

from volley.config import METRICS_ENABLED, METRICS_PORT, import_module_from_string
from volley.data_models import ComponentMessage, QueueMessage
from volley.logging import logger
from volley.queues import Queue, Queues, available_queues

ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)

# enables mocking the infinite loop to finite
RUN_ONCE = False


PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["process_name"])
MESSAGE_CONSUMED = Counter("messages_consumed_count", "Messages consumed from input", ["status"])  # success or fail
MESSAGES_PRODUCED = Counter("messages_produced_count", "Messages produced to output destination(s)", ["destination"])


def load_schema_class(q: Queue) -> Any:
    """loads the schema for a queue from config

    parses the string to the path of the model into and importable object

    for exampe: load a model from volley.default_config
        volley.data_models.ComponentMessage results in something equivalent to:
            ```
            from volley.data_models import ComponentMessage
            return ComponentMessage
            ```
    """
    if q.model_schema in ["dict"]:
        return dict
    else:
        return import_module_from_string(q.model_schema)


@dataclass
class Engine:
    """initializes configuration for input and output workers"""

    input_queue: str
    output_queues: List[str]

    def __post_init__(self) -> None:

        self.queues: Queues = available_queues()

        self.in_queue: Queue = self.queues.queues[self.input_queue].copy()

        self.out_queues: Dict[str, Queue] = {
            x: self.queues.queues[x] for x in self.output_queues if (len(self.output_queues) != 0)
        }

        try:
            self.out_queues["dead-letter-queue"] = self.queues.queues["dead-letter-queue"]
        except KeyError:
            # TODO: there should be a more graceful default behavior for schema violations and retries
            logger.warning(
                """
            Dead-letter-queue config not found. Messages with schema violations crash the application.
            Add a queue named "dead-letter-queue" to volley_config.yml
            """
            )

    def stream_app(  # noqa: C901
        self, func: Callable[[ComponentMessageType], List[Tuple[str, Any]]]
    ) -> Callable[..., Any]:
        @wraps(func)
        def run_component() -> None:
            if METRICS_ENABLED:
                start_http_server(port=METRICS_PORT)
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked
            self.in_queue.qcon = import_module_from_string(self.in_queue.consumer_class)(queue_name=self.in_queue.value)

            input_data_class: ComponentMessageType = load_schema_class(self.in_queue)

            for qname, q in self.out_queues.items():
                q.qcon = import_module_from_string(q.producer_class)(queue_name=q.value)

            # queue connections were setup above. now we can start to interact with the queues
            while True:
                _start_time = time.time()

                # read message off the specified queue
                in_message: QueueMessage = self.in_queue.qcon.consume(queue_name=self.in_queue.value)  # type: ignore

                outputs: List[Tuple[str, Optional[ComponentMessageType]]] = []
                # every queue has a schema - validate the data coming off the queue
                # we are using pydantic to validate the data.
                try:
                    serialized_message: ComponentMessageType = input_data_class.parse_obj(in_message.message)
                except ValidationError:
                    logger.exception(
                        f"""
                        Error validating message from {self.in_queue.value}"""
                    )
                    if "dead-letter-queue" not in self.out_queues:
                        outputs = [("n/a", None)]
                        logger.warning("DLQ not configured")
                    else:
                        outputs = [
                            ("dead-letter-queue", ComponentMessage.parse_obj(in_message.message))  # type: ignore
                        ]

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
                    self.in_queue.qcon.delete_message(  # type: ignore
                        queue_name=self.in_queue.value,
                        message_id=in_message.message_id,
                    )
                    MESSAGE_CONSUMED.labels("success").inc()
                else:
                    self.in_queue.qcon.on_fail()  # type: ignore
                    MESSAGE_CONSUMED.labels("fail").inc()
                _duration = time.time() - _start_time
                PROCESS_TIME.labels("cycle").observe(_duration)

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

        # used for unit testing as a means to access the wrapped component without the decorator
        run_component.__wrapped__ = func  # type: ignore
        return run_component
