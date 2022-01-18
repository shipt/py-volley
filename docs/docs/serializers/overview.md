# Serialization

Volley ships with two JSON serializers and one [MessagePack](https://msgpack.org/index.html) serializer.


## Supported Serializers
### JSON
- [`volley.serializers.OrJsonSerialization`](https://github.com/ijl/orjson): the *default* serializer
- [`volley.serializers.JsonSerialization`](https://docs.python.org/3/library/json.html) library

### MessagePack
- [`volley.serializers.MsgPackSerialization`](https://github.com/msgpack/msgpack-python)


## Extending Serialization with Plugins

Serialization can be extended with plugins. Serializers must do two things: `serialize` and `deserialize`. 

- `serialize`: covert a Python `dict` to `bytes`

- `deserialize`: convert `bytes` to a Python `dict`

You can build a plugin by subclassing `BaseSerialization` from `volley/serializers/base.py`
### Register the plugin

Like all configuration, they can be specified in either `yaml` or a `dict` passed directly to `volley.engine.Engine` (but not both).

```python
config = {
    "my_topic": {
        "value": "my_topic_name",
        "profile": "confluent",
        "serializer": "path.to.mySerializer"
    }
}
```
Or via yaml:

```yml
# ./my_volley_config.yml
queues:
  my_topic:
    value: my_topic_name
    type: kafka
    serializer: path.to.mySerializer
```