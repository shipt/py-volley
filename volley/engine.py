import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from prometheus_client import Counter, Summary, start_http_server

from volley.config import METRICS_ENABLED, METRICS_PORT
from volley.data_models import (
    ComponentMessage,
    ComponentMessageType,
    QueueMessage,
    schema_handler,
)
from volley.logging import logger
from volley.queues import (
    ConnectionType,
    DLQNotConfiguredError,
    Queue,
    apply_defaults,
    config_to_queue_map,
    dict_to_config,
    yaml_to_dict_config,
)
from volley.serializers.base import handle_serializer
from volley.util import GracefulKiller

# enables mocking the infinite loop to finite
RUN_ONCE = False


PROCESS_TIME = Summary("process_time_seconds", "Time spent running a process", ["volley_app", "process_name"])
MESSAGE_CONSUMED = Counter(
    "messages_consumed_count", "Messages consumed from input", ["volley_app", "status"]
)  # success or fail
MESSAGES_PRODUCED = Counter(
    "messages_produced_count", "Messages produced to output destination(s)", ["volley_app", "source", "destination"]
)

POLL_INTERVAL = 1


@dataclass
class Engine:
    """initializes configuration for input and output workers"""

    input_queue: str
    output_queues: List[str] = field(default_factory=list)

    app_name: str = "volley"
    dead_letter_queue: Optional[str] = None

    killer: GracefulKiller = GracefulKiller()

    # set in post_init
    queue_map: Dict[str, Queue] = field(default_factory=dict)

    queue_config: Optional[Dict[str, Any]] = None
    yaml_config_path: str = "./volley_config.yml"

    def __post_init__(self) -> None:
        """loads configurations and connectors"""
        if self.output_queues == []:
            logger.warning("No output queues provided")

        # if user provided config, use it
        if self.queue_config:
            cfg: dict[str, List[dict[str, str]]] = dict_to_config(self.queue_config)
        else:
            logger.info(f"loading configuration from {self.yaml_config_path}")
            cfg = yaml_to_dict_config(yaml_path=self.yaml_config_path)

        # handle DLQ
        if self.dead_letter_queue is not None:
            # if provided by user, DLQ becomes a producer target
            self.output_queues.append(self.dead_letter_queue)
        else:
            logger.warning("DLQ not provided. Application will crash on schema violations")

        cfg = apply_defaults(cfg)
        self.queue_map = config_to_queue_map(cfg["queues"])

        # validate input_queue, output_queues, and DLQ (optional) are valid configurations
        for q in [self.input_queue] + self.output_queues:
            if q not in self.queue_map:
                raise NameError(f"Queue '{q}' not found in configuration")

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
            # we only want to connect to queues passed in to Engine()
            # there can be more queues than we need defined in the configuration yaml
            for out_q_name in self.output_queues:
                self.queue_map[out_q_name].connect(con_type=ConnectionType.PRODUCER)

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
                    logger.info(f"No messages - sleeping {POLL_INTERVAL=}")
                    time.sleep(POLL_INTERVAL)
                    continue

                # typing for producing
                outputs: Optional[List[Tuple[str, ComponentMessage]]] = []

                # input serialization
                deserialized_msg: Any
                deserialized_success: bool = False
                dlq_message: str = "NONE"
                deserialized_msg, deserialized_success = handle_serializer(
                    serializer=input_con.serializer, operation="deserialize", message=in_message.message
                )

                validated_success: bool = False
                if deserialized_success:
                    # schema validation can only happen if deserialization succeeds
                    validated_message: ComponentMessageType
                    validated_message, validated_success = schema_handler(
                        schema=input_con.schema, message=deserialized_msg
                    )
                else:
                    # serialize failed, try to send this message to DLQ
                    dlq_message = in_message.message
                    logger.warning(f"{input_con.serializer=} failed")

                if not validated_success and deserialized_success:
                    logger.warning(f"schema '{input_con.schema=}' validation failed")
                    dlq_message = deserialized_msg

                if dlq_message == "NONE":
                    # happy path
                    pass
                elif self.dead_letter_queue in self.queue_map and dlq_message != "NONE":
                    # DLQ is configured and there is a message ready for the DLQ
                    outputs = [(self.dead_letter_queue, ComponentMessage(error_msg=dlq_message))]
                else:
                    # things have gone wrong w/ the message and no DLQ configured
                    raise DLQNotConfiguredError(f"Deserializing {in_message.message} failed")

                # component processing
                if not outputs:
                    # this is happy path
                    # if outputs have been assigned it means this message is destined for a DLQ
                    _start_main = time.time()
                    outputs = func(validated_message)
                    _fun_duration = time.time() - _start_main
                    PROCESS_TIME.labels(volley_app=self.app_name, process_name="component").observe(_fun_duration)

                all_produce_status: List[bool] = []
                if outputs is None:
                    # assume a "None" output is a successful read of the input
                    all_produce_status.append(True)
                else:
                    for qname, component_msg in outputs:
                        if component_msg is None:
                            # this is deprecated: components should just return None
                            continue

                        try:
                            out_queue = self.queue_map[qname]
                        except KeyError as e:
                            raise NameError(f"App not configured for output queue {e}")

                        # prepare and validate output message
                        if not isinstance(component_msg, out_queue.schema) and out_queue.schema is not None:
                            raise TypeError(
                                f"{out_queue.name=} expected '{out_queue.schema}' - object is '{type(component_msg)}'"
                            )

                        try:
                            # serialize message
                            serialized = out_queue.serializer.serialize(component_msg.dict())
                            status = out_queue.producer_con.produce(queue_name=out_queue.value, message=serialized)
                            MESSAGES_PRODUCED.labels(
                                volley_app=self.app_name, source=input_con.name, destination=qname
                            ).inc()
                        except Exception:
                            logger.exception(f"failed producing message to {out_queue.name}")
                            status = False
                        all_produce_status.append(status)

                if all(all_produce_status):
                    # TODO - better handling of success criteria
                    # if multiple outputs - how to determine if its a success if one fails
                    input_con.consumer_con.delete_message(
                        queue_name=input_con.value,
                        message_id=in_message.message_id,
                    )
                    MESSAGE_CONSUMED.labels(volley_app=self.app_name, status="success").inc()
                else:
                    input_con.consumer_con.on_fail()
                    MESSAGE_CONSUMED.labels(volley_app=self.app_name, status="fail").inc()
                _duration = time.time() - _start_time
                PROCESS_TIME.labels(volley_app=self.app_name, process_name="cycle").observe(_duration)

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
