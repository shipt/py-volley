# Run locally
1. Install poetry with `pip install poetry` or follow [poetry's official documentaton](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions)

2. Acquire creds to pypi.shipt.com #ask-machine-learning

3. Export these to your shell 

```bash
export POETRY_HTTP_BASIC_SHIPT_USERNAME=your_username
export POETRY_HTTP_BASIC_SHIPT_PASSWORD=your_password
```

# CI / CD

This is a [Kubedashian](https://kubedashian.shipt.com/apps/ml-bundle-engine) project. 

See `.drone.yml` for build and test gates and Concourse for deployment status.
Refer to infraspec.yml for infrastructure and dedployment definition criteria.

# Monitoring

Production and Staging queue size [Grafana dashboards](https://metrics.shipt.com/d/5dtDxKK7k/ml-bundle-engine-queues) 

## Testing

`make test.unit` Runs unit tests on individual components with mocked responses dependencies external to the code. Docker is not involved in this process.

`make test.integration` Runs all components, Postgres, Kafka, and Redis in locally running Docker containers. Validates messages published to input topic successfully reach the output topic.

# Components

Components get implemented as a function decorated with the `bundle_engine`. A component consumes from one queue and can publish to one or many queues. 

A component function takes in `input_object` of type: `ComponentMessage`, which is a Pydantic model that accepts extra attributes. This model defines the schema of messages on the INPUT_QUEUE. The component function can process and modify that object it meet its needs.

Components output a list of tuples, where the tuple is defined as `(<name_of_queue>, ComponentMessage)`.
 The returned component message type must agree with the type accepted by the queue you are publishing to.

### Generic Example:

Let's define three queues, `my_input`, `queue_a`, `queue_b` and assume `my_input` is a Kafka topic populated by some external service. Let's decide that `queue_a` is an RSMQ type and `queue_b` is a Postgres. We define these in `engine/config.yml`. Queues have `names`, which is how we reference them and `values`. The engine interacts with the queue using the value and components (developers) interact with queue using the `name`.

Queues also have a schema. These are defined by subclassing `engine.data_models.ComponentMessage`. `ComponentMessage` are Pydantic models that accept extra attributes. This means if you do not provide a strictly subclass to a `ComponentMessage`, the message will get passed through to your component as key-value pairs from a `dict` of message on the queue, and constructed via `ComponentMessage(**message)`. The location of the data model for a queue is defined as the value of the `schema` attribute in the config file.

```yml
# engine/config.yml
queues:
  - name: my_input
    value: "stg.bus.kafka.topic.name"
    type: kafka
    schema: components.data_models.InputMessage
  - name: queue_a
    value: queue_a
    type: rsmq
    schema: components.data_models.MessageA
  - name: queue_b
    value: name_of_table
    type: postgres
    schema: components.data_models.MessageA
```

As mentioned above, schemas for queue are defined by subclassing `ComponentMessage`.

```python
# components/data_models.py
from engine.data_models import ComponentMessage

class InputMessage(ComponentMessage):
    list_of_values: List[float]


class MessageA(ComponentMessage):
    mean_value: float

class MessageB(ComponentMessage):
    max_value: float
```

`my_component` is implemented below. It consumes from `my_input` and publishes to `queue_a` and `queue_b` (defined above).


```python
# components/my_component.py
from engine.engine import bundle_engine

import numpy as np

@bundle_engine(input_queue="my_input", output_queues=["queue_a", "queue_b"])
def my_component_function(input_object: ComponentMessage) -> List[(str, ComponentMessage)]
    """component function that computes some basics stats on a list of values
    
    Consumes from a queue named "my_input".
    Publishes to two queues, "queue_a", "queue_b"
    """

    # we can access the input models attributes like any other pydantic model
    mean_value = np.mean(input_object.list_of_values)

    # or convert to a dict
    input_dict = input_object.dict()
    max_value = max(input_object["list_of_values"])

    # queue_a expects an object of type MessageA
    output_a = MessageA(mean_value=mean_value)

    # queue_b expects an object of type MessageB
    output_b = MessageB(max_value=max_value)

    # send the messages to the specificed queues
    return [
        ("queue_a", output_a),
        ("queue_b", output_b)
    ]
```

Components are run as stand-alone workers.

```python
# main.py
from components import my_component_function
my_component_function()
```

And are run by invoking the function.
```bash
python main.py
```

# Engine Design

## Engine

The engine itself is a python decorator that wraps a component worker and runs as headless services. The engine interacts with `Connectors`, `QueueMessages`, and the component function that it wraps.

On initialization:
- setup connections to the queues using the connectors specified by the components inputs and outputs
- determines the data type required by the component

Once the engine has initialized, it will continuously poll the input queue for new messages. When it receives a message, it will process the message and pass it to the wrapped component function. It takes the output of the component function and produces it to the output queues. It will repeat this process until terminated.

## Connectors

Connectors are specific implementations of producers and consumers. There are currently connectors for pyRSMQ, Postgres, and Kafka. For example - `produce` in a Postgres connector handles inserting a row to a table, while `produce` in a Kafka connector handles producing a message to a topic.

Consumers and producers handle converting the `QueueMessage` objects to whichever data type and serialization is implemented in the specfic queue. For example, the pyRSMQ implementation stores messages as `JSON`, so the pyRSMQ producer converts the message in `QueueMessage` to JSON, then places the message on the queue. Likewise, pyRMSQ consumer read from JSON and convert to `QueueMessage`.

## Producers/Consumers

Components consume from one queue and produce to one or many queues. The engine has a consistent interface to conduct the following operations on any of the supported queues:

Producers:
- `produce` - place a message on the queue.

Consumers:

- `consume` - pull a message off the queue.

- `delete` - delete a message on the queue.

- `on_fail` - operation to conduct if a component worker fails processing a message. For example, place the message back on the queue, rollback a transaction, etc.

## Queues

Queues are the broker and backend that handle messages. The bundle engine supports types of queues; [pyRSMQ](https://github.com/mlasevich/PyRSMQ), Kafka, and Postgres. Each technology can be used as a first-in-first-out basis but also have unique features and limitations.

RSMQ is the python implementation of the [RSMQ](https://github.com/smrchy/rsmq) project. It is lightweight but full features message queue system built on Redis. It provides clean interface to producing and consuming messages from a queue. It only supports strict FIFO - you cannot modify or update a message on the queue once it is produced. The number of messages that can exist in the queue is limited by the amount of memory available to Redis.

Kafka - TODO

Postgres - TODO
