# Data validation


## Overview
Model handlers live between serialization and the application and handle converting data to a model that your application is expecting to consume. Post processing from the application, they convert data to a format which can be serialized by a serialization handler. Model handlers can handle both serialization and model construction if serialization is disabled in configuration by setting `serializer: None|disabled`. 

`PydanticModelHandler` calls `.parse_obj()` on the user provided Pydantic model, which takes in a `dict` then validates the data and creates the instance of the Pydantic model.

`PydanticParserModelHandler` calls `.parse_raw()` on the user provided Pydantic model, which takes in `str|bytes` and parses to json before validating and creating and instance of the Pydantic model.

`volley.models.PydanticParserModelHandler` is an example of a model handler that also conducts serialization.

## Example
All model handlers inherit from `BaseModelHandler`. They need to construct and deconstruct a data model. To illustrate, we will use the following example:

- KafkaConsumer consumed message from topic as bytes: b'{"hello": "world"}'

- JSONSerializer converts the bytes to dict: {"hello":"world"}

- PydanticModelHandler is the default handler. User creates Pydantic models for input and output data with the following definition:


```python
from pydantic import BaseModel

class myIncomingData(BaseModel):
    hello: str
class myOutgoingData(BaseModel):
    foo: str
```

This model is registered in configuration:
```python
config = {
    "input-queue":{
        ...,
        "data_model": "mymodels.myIncomingData"
    },
    "output-queue":{
        ...,
        "data_model": "mymodels.myOutgoingData"
    },  
}
```

Volley uses the `PydanticModelHandler` to construct an instance of `myIncomingData` using `message` data. When the message is incoming to the application, `PydanticModelHandler.construct()` is called with `myIncomingData` and the incoming `message` (deserialized to dict from orjson). This effectively becomes the following operation:

```python
incoming_model = myModel.parse_obj(message)
```
`incoming_model: myModel` is passed to the application for processing.

The user constructs the outgoing message in their application function and returns it to Volley:
```python
out_message = myOutgoingData(foo="bar")
return [("output-queue", out_message)]
```

Volley then uses `PydanticModelHandler` to `deconstruct` `myOutgoingData` to a `dict` which is then passed to `orjson` for serialization, finally to Kafka via the connector.


## Extending Models

A model handler can be defined to construct any data model so long as it is compliant with the signature of `BaseModelHandler` and the configured serializer is selected in configuration. To further illustrate, if one were to disable serialization and use `PydanticParserModelHandler`, constructing a data model would effectively become:

```python
incoming_model = myModel.parse_raw(message)
```

and deconstructing the data would become:

```python
outgoing_message = outgoing_model.json().encode("utf-8")
```
