from typing import List, Tuple

from example.protos.compiled import messages_pb2
from volley.engine import Engine

# configure the Kafka topics
queue_config = {
    "input-topic": {
        "value": "incoming.kafka.topic",
        "type": "kafka",
        "model_handler": "volley.models.proto_model.ProtoModelHandler",
        "serializer": None,
        "schema": "example.protos.compiled.messages_pb2.Person",
    },
    "output-topic": {
        "value": "outgoing.kafka.topic",
        "type": "kafka",
        "model_handler": "volley.models.proto_model.ProtoModelHandler",
        "serializer": None,
        "schema": "example.protos.compiled.messages_pb2.Person",
    },
    # optionally - configure a dead-letter-queue
    "dead-letter-queue": {
        "value": "deadletter.kafka.topic",
        "type": "kafka",
        "model_handler": "volley.models.proto_model.ProtoModelHandler",
        "serializer": None,
        "schema": "example.protos.compiled.messages_pb2.Person",
    },
}

# intializae the Volley application
app = Engine(
    app_name="my_volley_app",
    input_queue="input-topic",
    output_queues=["output-topic"],
    dead_letter_queue="dead-letter-queue",
    queue_config=queue_config,
)


# decorate your function
@app.stream_app
def my_app(msg: messages_pb2.Person) -> List[Tuple[str, messages_pb2.Person]]:

    msg.name = f"echo {msg.name}"
    return [("output-topic", msg)]


if __name__ == "__main__":
    my_app()
