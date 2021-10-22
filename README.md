[![Build Status](https://drone.shipt.com/api/badges/shipt/ml-bundle-engine/status.svg)](https://drone.shipt.com/shipt/ml-bundle-engine)

# ML Bundle Engine
The ML bundle engine is an event driven series of processes & queues. 
The engine consumes a Kafka message containing a list of orders from the bundle request topic, enriches the orders by calling various machine learning models, then using one or more optimization services to group the orders into bundles. The bundles are produced to another Kafka topic.

# Run locally
Acquire creds to pypi.shipt.com #ask-machine-learning

Add these to your shell

```bash
export POETRY_HTTP_BASIC_SHIPT_USERNAME=your_username
export POETRY_HTTP_BASIC_SHIPT_PASSWORD=your_password
```

Start all services and data stores
`make run`

Stop all services and data stores
`make stop`

- dummy_events: components/dummy_events.py - produces dummy kafka messages to an `input-topic` kafka
- features: components/feature_generator.py - reads from `input-topic` kafka, publishes to `triage` queue
- triage: components/triage.py - reads from `triage` queue, publishes to `optimizer` queue
- optimizer: components/optimizer.py - reads from `optimizer` queue, publishes to `collector` or back to `optimizer` queue
- fallback: components/fallback.py - reads from `fallback` queue, publishes to `collector` queue
- collector: components/collector.py - reads from `collector` queue and publishes to `output-topic` kafka
- dummy_consumer: components/dummy_consimer.py - reads from `output-topic` kafka and logs to stddout

## Simulating Staging Data

`make notebook` will spin up jupyer notebook. Open `./notebooks/publish_consume.ipynb`. Publish messages to the input topic and then consume data from the output topic.


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

Any be run by invoking the function.
```bash
python main.py
```

# TODO: Engine Design
## Queues

## Producers/Consumers
## Connectors

## Data Stores