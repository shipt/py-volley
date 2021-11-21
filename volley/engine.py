import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from prometheus_client import Counter, Summary, start_http_server
from pydantic import ValidationError

from volley.config import METRICS_ENABLED, METRICS_PORT
from volley.data_models import ComponentMessage, ComponentMessageType, QueueMessage
from volley.logging import logger
from volley.queues import (
    ConnectionType,
    Queue,
    apply_defaults,
    config_to_queue_map,
    dict_to_config,
    yaml_to_dict_config,
)
from volley.util import GracefulKiller

# enables mocking the infinite loop to finite
RUN_ONCE = False


PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["process_name"])
MESSAGE_CONSUMED = Counter("messages_consumed_count", "Messages consumed from input", ["status"])  # success or fail
MESSAGES_PRODUCED = Counter("messages_produced_count", "Messages produced to output destination(s)", ["destination"])

POLL_INTERVAL = 1


@dataclass
class Engine:
    """initializes configuration for input and output workers"""

    input_queue: str
    output_queues: List[str]
    dead_letter_queue: Optional[str] = None

    killer: GracefulKiller = GracefulKiller()

    # set in post_init
    queue_map: Dict[str, Queue] = field(default_factory=dict)

    queue_config: Optional[Dict[str, Any]] = None
    yaml_config_path: str = "./volley_config.yml"

    def __post_init__(self) -> None:
        self._construct_queues()

    def _construct_queues(self) -> None:
        """loads configurations and connectors"""
        # if user provided config, use it
        if self.queue_config:
            cfg: dict[str, List[dict[str, str]]] = dict_to_config(self.queue_config)
        else:
            logger.info(f"loading configuration from {self.yaml_config_path}")

            # handle DLQ
            if self.dead_letter_queue is not None:
                # if provided by user, DLQ becomes a producer target
                self.output_queues.append(self.dead_letter_queue)
            else:
                logger.warning("DLQ not provided. Application will crash on schema violations")

            cfg = yaml_to_dict_config(yaml_path=self.yaml_config_path)
        cfg = apply_defaults(cfg)
        self.queue_map = config_to_queue_map(cfg["queues"])
        logger.info(f"Queues initialized: {list(self.queue_map.keys())}")

    def stream_app(  # noqa: C901
        self, func: Callable[[Union[ComponentMessageType, Any]], Optional[List[Tuple[str, Any]]]]
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
            for out_q_name in self.output_queues:
                self.queue_map[out_q_name].connect(con_type=ConnectionType.PRODUCER)
                self.queue_map[out_q_name].init_schema()

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
                    serialized_message: Union[ComponentMessageType, Dict[Any, Any]] = self.queue_map[  # type: ignore
                        self.input_queue
                    ].model_class(**in_message.message)
                except ValidationError:
                    logger.exception(
                        f"""
                        Error validating message from {input_con.value}"""
                    )
                    if self.dead_letter_queue not in self.queue_map:
                        logger.error("DLQ not configured. Processing will fail")
                        raise NotImplementedError
                    else:
                        outputs = [(self.dead_letter_queue, ComponentMessage.parse_obj(in_message.message))]

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

                        try:
                            status = out_queue.producer_con.produce(queue_name=out_queue.value, message=q_msg)
                            MESSAGES_PRODUCED.labels(destination=qname).inc()
                        except Exception:
                            logger.exception("failed producing message")
                            status = False
                        all_produce_status.append(status)

                if all(all_produce_status):
                    # TODO - better handling of success criteria
                    # if multiple outputs - how to determine if its a success if one fails
                    input_con.consumer_con.delete_message(
                        queue_name=input_con.value,
                        message_id=in_message.message_id,
                    )
                    MESSAGE_CONSUMED.labels("success").inc()
                else:
                    input_con.consumer_con.on_fail()
                    MESSAGE_CONSUMED.labels("fail").inc()
                _duration = time.time() - _start_time
                PROCESS_TIME.labels("cycle").observe(_duration)

                if RUN_ONCE:
                    # for testing purposes only - mock RUN_ONCE
                    break

            # graceful shutdown of ALL queues
            logger.info(f"Shutting down {input_con.value}")
            input_con.consumer_con.shutdown()
            for q_name in self.output_queues:
                out_queue = self.queue_map[q_name]
                logger.info(f"Shutting down {out_queue.value}")
                out_queue.producer_con.shutdown()
                logger.info(f"{q_name} shutdown complete")

        # used for unit testing as a means to access the wrapped component without the decorator
        run_component.__wrapped__ = func  # type: ignore
        return run_component
