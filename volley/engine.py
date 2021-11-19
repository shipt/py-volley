import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from prometheus_client import Counter, Summary, start_http_server
from pydantic import ValidationError

from volley.config import METRICS_ENABLED, METRICS_PORT, import_module_from_string
from volley.data_models import ComponentMessage, QueueMessage
from volley.logging import logger
from volley.queues import ConnectionType, Queue, queues_from_yaml
from volley.util import GracefulKiller

ComponentMessageType = TypeVar("ComponentMessageType", bound=ComponentMessage)

# enables mocking the infinite loop to finite
RUN_ONCE = False


PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["process_name"])
MESSAGE_CONSUMED = Counter("messages_consumed_count", "Messages consumed from input", ["status"])  # success or fail
MESSAGES_PRODUCED = Counter("messages_produced_count", "Messages produced to output destination(s)", ["destination"])

DLQ_NAME = "dead-letter-queue"
POLL_INTERVAL = 1

def load_schema_class(q: Queue) -> Any:
    """loads the schema for a queue from config
    "dict" is an acceptable schema
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

    killer: GracefulKiller = GracefulKiller()

    # user can provide a full configuration in Engine(), or use volley_config.yml, but not both
    queue_config: Optional[Dict[str, Any]] = None

    # set in post_init
    queue_map: Dict[str, Queue] = field(default_factory=dict)

    # set in post_init
    dlq_enabled: bool = field(init=False, default=False)

    def __post_init__(self) -> None:

        # dict of <queue_name>: Queue
        self.queue_map = queues_from_yaml(queues=[self.input_queue] + self.output_queues)

        if DLQ_NAME not in self.queue_map:
            try:
                self.queue_map.update(queues_from_yaml([DLQ_NAME]))
                self.output_queues.append(DLQ_NAME)
                self.dlq_enabled = True
            except Exception:
                self.dlq_enabled = False
                # TODO: there should be a more graceful default behavior for schema violations and retries
                logger.warning(
                    f"""
                Dead-letter-queue config not found. Messages with schema violations crash the application.
                Add a queue named "{DLQ_NAME}" to volley_config.yml
                """
                )

    def stream_app(  # noqa: C901
        self, func: Callable[[ComponentMessage], Optional[List[Tuple[str, Any]]]]
    ) -> Callable[..., Any]:
        @wraps(func)
        def run_component() -> None:
            if METRICS_ENABLED:
                start_http_server(port=METRICS_PORT)
            # the component function is passed in as `func`
            # first setup the connections to the input and outputs queues that the component will need
            # we only want to set these up once, before the component is invoked

            # intialize connections to each queue, and schemas
            self.queue_map[self.input_queue].connect(con_type=ConnectionType.CONSUMER)
            self.queue_map[self.input_queue].init_schema()
            # we only want to connect to queues passed in to Engine()
            # there can be more queues than we need defined in the configuration yaml
            for out_queue in self.output_queues:
                self.queue_map[out_queue].connect(con_type=ConnectionType.PRODUCER)
                self.queue_map[out_queue].init_schema()

            # queue connections were setup above. now we can start to interact with the queues
            # alias for input connection readability
            input_con = self.queue_map[self.input_queue]
            while not self.killer.kill_now:
                _start_time = time.time()

                # read message off the specified queue
                in_message: Optional[QueueMessage] = input_con.consumer_con.consume(queue_name=input_con.value)
                if in_message is None:
                    # if no messages, handle poll interval
                    # TODO: this should be dynamic with some sort of backoff
                    time.sleep(POLL_INTERVAL)
                    continue

                outputs: Optional[List[Tuple[str, ComponentMessage]]] = []
                # every queue has a schema - validate the data coming off the queue
                # we are using pydantic to validate the data.
                try:
                    serialized_message: ComponentMessage = self.queue_map[self.input_queue].model_class.parse_obj(
                        in_message.message
                    )
                    # serialized_message: ComponentMessageType = input_data_class.parse_obj(in_message.message)
                except ValidationError:
                    logger.exception(
                        f"""
                        Error validating message from {input_con.value}"""
                    )
                    if not self.dlq_enabled:
                        outputs = None
                        logger.error("DLQ not configured. Skipping message")
                    else:
                        outputs = [(DLQ_NAME, ComponentMessage.parse_obj(in_message.message))]

                if not outputs:
                    _start_main = time.time()
                    outputs = func(serialized_message)
                    _fun_duration = time.time() - _start_main
                    PROCESS_TIME.labels("component").observe(_fun_duration)

                all_produce_status: List[bool] = []
                if outputs is None:
                    # assume a "None" output is a successful read of the input
                    all_produce_status.append(True)
                else:
                    for qname, component_msg in outputs:
                        if component_msg is None:
                            # this is deprecated: components should just return None
                            continue
                        q_msg = QueueMessage(message_id=None, message=component_msg.dict())

                        try:
                            out_queue = self.queue_map[qname]
                        except KeyError:
                            logger.exception(f"{qname} is not defined in this component's output queue list")

                        # TODO: typing of engine.queues.Queue.qcon makes this ambiguous and potentially error prone
                        try:
                            status = out_queue.producer_con.produce(queue_name=out_queue.value, message=q_msg)  # type: ignore
                            MESSAGES_PRODUCED.labels(destination=qname).inc()
                        except Exception:
                            logger.exception("failed producing message")
                            status = False
                        all_produce_status.append(status)

                if all(all_produce_status):
                    # TODO - better handling of success criteria
                    # if multiple outputs - how to determine if its a success if one fails
                    input_con.consumer_con.delete_message(  # type: ignore
                        queue_name=input_con.value,
                        message_id=in_message.message_id,
                    )
                    MESSAGE_CONSUMED.labels("success").inc()
                else:
                    input_con.consumer_con.on_fail()  # type: ignore
                    MESSAGE_CONSUMED.labels("fail").inc()
                _duration = time.time() - _start_time
                PROCESS_TIME.labels("cycle").observe(_duration)

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

            # graceful shutdown of ALL queues
            logger.info(f"Shutting down {input_con.value}")
            input_con.consumer_con.shutdown()  # type: ignore
            for q_name in self.output_queues:
                out_queue = self.queue_map[q_name]
                logger.info(f"Shutting down {out_queue.value}")
                out_queue.producer_con.shutdown()  # type: ignore
                logger.info(f"{q_name} shutdown complete")

        # used for unit testing as a means to access the wrapped component without the decorator
        run_component.__wrapped__ = func  # type: ignore
        return run_component
