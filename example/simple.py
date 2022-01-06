from typing import List, Tuple

from pydantic import BaseModel

from volley.engine import Engine


# define data models for the incoming and outgoing data
class InputMessage(BaseModel):
    """validate the incoming data"""

    list_of_values: List[float]


class OutputMessage(BaseModel):
    """validate the outgoing data"""

    max_value: float


# configure the Kafka topics
queue_config = {
    "input-topic": {
        "value": "incoming.kafka.topic",
        "profile": "confluent",
        "data_moodel": "InputMessage",
    },
    "output-topic": {
        "value": "outgoing.kafka.topic",
        "profile": "confluent",
        "data_moodel": "OutputMessage",
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
def my_app(msg: InputMessage) -> List[Tuple[str, OutputMessage]]:
    max_value = max(msg.list_of_values)
    output = OutputMessage(max_value=max_value)

    # send the output object to "output-topic"
    # as defined on `queue_config`
    return [("output-topic", output)]


if __name__ == "__main__":
    my_app()
