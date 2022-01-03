# Profiles


## Overview
Profiles are pre-defined sets of Volley configurations and can be partially or completely overridden. 


For example, to use to [confluent](#confluent) profile:

```python hl_lines="5 12"
from volley import Engine

config = {
    "my-input-queue": {
        "profile": "confluent",
        "value": "my.kafka.topic",
    }
}

app = Engine(
    input_queue="my-input-queue,
    queue_config=config
)

```

Profiles define the following:

`consumer`
: (str) : dot path to the concrete implementation of the base [Consumer](./connectors/base.md#consumer). Consumers define how Volley should consume a message from a queue and mark a message as successfully read and processed.

`producer`
: (str) : dot path to the concrete implementation of the base [Producer](./connectors/base.md#consumer). Defines how Volley should produce a message to a queue.

`serializer`
: (str) : dot path to the concrete implementation of the base [BaseSerialization](./serializers/base.md#serialization). Defines how to turn raw `bytes` into a primative python object.

`data_model`
: (str) : dot path to a user provided data model. For example, a Pydantic data model, or a NamedTuple.

`model_handler`
: (str) : dot path to the concrete implementation of [BaseModelHandler](./serializers/base.md#serialization). Defines how Volley should turn serialized data into a user provided data model.

## Usage

Specify a profile from the list of [supported profiles](#supported-profiles) in the initialization configuration.

```python hl_lines="3"
config = {
    "my-input-queue": {
        "profile": "confluent",
        "value": "my.kafka.topic",
    }
}
```

If you wish to override any of of the configuration values from the "confluent" profile, just specify them.
```python
# /path/to/myAppDataModels.py
from pydantic import BaseModel

class myModel(BaseModel):
    my_str: str
```

```python hl_lines="5"
config = {
    "my-input-queue": {
        "profile": "confluent",
        "value": "my.kafka.topic",
        "data_model": "path.to.myAppDataModels.myModel"
    }
}
```

Or use MessagePack for serialization:

```python hl_lines="6"
config = {
    "my-input-queue": {
        "profile": "confluent",
        "value": "my.kafka.topic",
        "data_model": "path.to.myAppDataModels.myModel",
        "serializer": "volley.serializers.msgpack_serializer.MsgPackSerialization",
    }
}
```


## User Defined Configuration

Profiles can be partially or completely overriden and are not explicitly required. If you do not provide a value for `profile`, you will need to provide valid configuration values for each of `consumer`, `producer`, `serializer`, `model_handler`, and `data_model`. These could be dot paths to your own custom implementations, or configurations that already exist in Volley.

For example:

```python hl_lines="3"
from volley import Engine

config = {
    "my-input-queue": {
        "profile": "confluent",
        "value": "my.kafka.topic",
    }
}

app = Engine(
    input_queue="my-input-queue,
    queue_config=config
)

```

Is equivalent to:

```python hl_lines="4-8"
config = {
    "my-input-queue": {
        "value": "my.kafka.topic",
        "consumer": "volley.connectors.confluent.ConfluentKafkaConsumer",
        "producer": "volley.connectors.confluent.ConfluentKafkaProducer",
        "model_handler": "volley.models.PydanticModelHandler",
        "data_model": "volley.data_models.GenericMessage",
        "serializer": "volley.serializers.orjson_serializer.OrJsonSerialization",
    }
}
```

Refer to [Extending Volley](extending.md) for instructions on writing your own [Connectors](connectors/overview.md), [Serializers](serializers/overview.md), and [Model Handlers](models/overview.md). All of the attributed provided by a profile can be overridden with existing or custom implementations.

## Supported Profiles

### confluent

The default conlfuent profile is most commonly used for applications working with Confluent Kafka brokers. It heavily relies on [librdkafka](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) and follows at-least-once delviery semantics by default. Consumed message offsets are auto-committed back to the Kafka broker. Messages are consumed from the Kafka broker as `bytes`, and serialized using `orjson`, and constructed into a generic Pydantic model. Many uses will provide their own value for `data_model` rather than using a generic Pydantic model.

| key           | value                                                    | link |
| --------------| -------------------------------------------------------- | ---- |
| consumer      | volley.connectors.confluent.ConfluentKafkaConsumer       | [docs](connectors/kafka.md#confluentkafkaconsumer)
| producer      | volley.connectors.confluent.ConfluentKafkaProducer       | [docs](connectors/kafka.md#confluentkafkaproducer)
| data_model    | volley.data_models.GenericMessage                      | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                       | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.orjson_serializer.OrJsonSerialization | [docs](serializers/OrJsonSerialization.md)


### confluent-pydantic

Very similar to the `confluent` profile. This profile uses Pydantic's default serializer mechanism to convert `bytes` to the Pydantic model.


| key           | value                                                    | link |
| --------------| -------------------------------------------------------- | ---- |
| consumer      | volley.connectors.confluent.ConfluentKafkaConsumer       | [docs](connectors/kafka.md#confluentkafkaconsumer)
| producer      | volley.connectors.confluent.ConfluentKafkaProducer       | [docs](connectors/kafka.md#confluentkafkaproducer)
| data_model    | volley.data_models.GenericMessage                      | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticParserModelHandler                 | [docs](models/PydanticParserModelHandler.md)
| serializer    | None |


### confluent-orjson-pydantic

| key           | value                                                    | link |
| --------------| -------------------------------------------------------- | ---- |
| consumer      | volley.connectors.confluent.ConfluentKafkaConsumer       | [docs](connectors/kafka.md#confluentkafkaconsumer)
| producer      | volley.connectors.confluent.ConfluentKafkaProducer       | [docs](connectors/kafka.md#confluentkafkaproducer)
| data_model    | volley.data_models.GenericMessage                      | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                       | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.orjson_serializer.OrJsonSerialization | [docs](serializers/OrJsonSerialization.md)


### confluent-msgpack-pydantic

Parses a message as `bytes` from the Kafka broker. Serializes using MessagePack then constructs a Pydantic Model.

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.confluent.ConfluentKafkaConsumer         | [docs](connectors/kafka.md#confluentkafkaconsumer)
| producer      | volley.connectors.confluent.ConfluentKafkaProducer         | [docs](connectors/kafka.md#confluentkafkaproducer)
| data_model    | volley.data_models.GenericMessage                        | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                         | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.msgpack_serializer.MsgPackSerialization | [docs](serializers/MsgPackSerialization.md)


### rsmq

The default Profile for interacting with pyRSMQ. Consumes a message from a Redis Simple Message Queue as `bytes`. Serializes with `orjson` and constructs a generic Pydantic model. The consumer deletes the consumed message once it is successfully processed. Messages that fail to parse or process are placed back on the originating queue, either explicitly by the consumer or by the queue itself after the visibility timeout expires.

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.rsmq.RSMQConsumer                        | [docs](connectors/rsmq.md#rsmqconsumer)
| producer      | volley.connectors.rsmq.RSMQProducer                        | [docs](connectors/rsmq.md#rsmqproducer)
| data_model    | volley.data_models.GenericMessage                        | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                         | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.orjson_serializer.OrJsonSerialization   | [docs](serializers/OrJsonSerialization.md)


### rsmq-pydantic

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.rsmq.RSMQConsumer                        | [docs](connectors/rsmq.md#rsmqconsumer)
| producer      | volley.connectors.rsmq.RSMQProducer                        | [docs](connectors/rsmq.md#rsmqproducer)
| data_model    | volley.data_models.GenericMessage                        | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticParserModelHandler                   | [docs](models/PydanticParserModelHandler.md)
| serializer    | None |


### rsmq-orjson-pydantic

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.rsmq.RSMQConsumer                        | [docs](connectors/rsmq.md#rsmqconsumer)
| producer      | volley.connectors.rsmq.RSMQProducer                        | [docs](connectors/rsmq.md#rsmqproducer)
| data_model    | volley.data_models.GenericMessage                        | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                         | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.orjson_serializer.OrJsonSerialization   | [docs](serializers/OrJsonSerialization.md)

### rsmq-msgpack-pydantic

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.rsmq.RSMQConsumer                        | [docs](connectors/rsmq.md#rsmqconsumer)
| producer      | volley.connectors.rsmq.RSMQProducer                        | [docs](connectors/rsmq.md#rsmqproducer)
| data_model    | volley.data_models.GenericMessage                        | [docs](models/data_models.md#genericmessage)
| model_handler | volley.models.PydanticModelHandler                         | [docs](models/PydanticModelHandler.md)
| serializer    | volley.serializers.msgpack_serializer.MsgPackSerialization | [docs](serializers/MsgPackSerialization.md)


### confluent-dlq

Dead-letter-queue configuration to Confluent Lafka. Does not serialize or construct a data model for data consumed or produced. Generally only uses as a producer.


| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.confluent.ConfluentKafkaConsumer         | [docs](connectors/kafka.md#confluentkafkaconsumer)
| producer      | volley.connectors.confluent.ConfluentKafkaProducer         | [docs](connectors/kafka.md#confluentkafkaproducer)
| serializer    | None |
| data_model    | None |
| model_handler | None |

### rsmq-dlq

Dead-letter-queue configuration to pyRSMQ. Does not serialize or construct a data model for data consumed or produced. Generally only uses as a producer.

| key           | value                                                      | link |
| --------------| ---------------------------------------------------------- | ---- |
| consumer      | volley.connectors.rsmq.RSMQConsumer                        | [docs](connectors/rsmq.md#rsmqconsumer)
| producer      | volley.connectors.rsmq.RSMQProducer                        | [docs](connectors/rsmq.md#rsmqproducer)
| serializer    | None |
| data_model    | None |
| model_handler | None |