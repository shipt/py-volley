# Metrics

Volley exposes [Prometheus metrics](https://prometheus.io/docs/concepts/metric_types/) on an http server. The metrics serving port can be configured or disabled completely.

Expose metrics on port 8081.

```python
from volley import Engine
app = Engine(
    ...
    metrics_port=8081
)
```

To disable:
```python
from volley import Engine
app = Engine(
    ...
    metrics_port=None # disabled
)
```

All metrics contain the label `volley_app` which is directly tied to the `app_name` parameter passed in when initializing `volley.Engine()`. Below are descriptions of each of the metrics produced by Volley.

## `messages_consumed_count` 
- Type: [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) 
- increments each time a message is consumed by the worker.
- Labels:
    - `status` : `success|fail`. If the worker consumes a message, but fails the corresponding produce operation, the message gets marked as a `fail`. Otherwise, it is a `success`.


## `messages_produced_count` 
- Type: [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)
- increments each time a message is produced
- Labels:
    - `source` : name of the queue the worker consumed from.
    - `destination` : name of the queue the message was produced to.


## `process_time_seconds` 
- Type: [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- observed amount of time various processes take to run
- Labels:
    - `process_name` : name of the process that is tracked
        - Values:
            - `component` : time associated with the processing time for the function that Volley wraps. This is isolated to the logic in the user's function.
            - `cycle` : one full cycle of consume message, serialize, schema validation, component processing, and publishing to all outputs. `component` is a subset of `cycle`

## `data_model_process_seconds`
- Type: [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- observed time for serialization/deserialization and data model construct/deconstruct
- Labels:
    - `process` : the observed process
        - Values: `deserialize`, `serialize`, `construct`, `deconstruct` 

## `redis_process_time_seconds` 
- Type: [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- similar to `process_time_seconds` but is isolated to the RSMQ connector.
- Labels:
    - `operation`: name of the operation.
        - Values
            - `read` : time to read a message from the queue
            - `delete` : time to delete a message from the queue
            - `write` : time to add a message to the queue

## `heartbeats`
- Type: [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)
- Counter is incremented at the start of each poll cycle. It is incremented more frequently when messages are consumed and at the rate of the `volley.Engine` `poll_interval` when no messages are available to be consumed.
- Labels: There are no labels on this metric.

Applications can export their own metrics as well. Examples in the Prometheus official [python client](https://github.com/prometheus/client_python) are a great place to start. The Volley exporter will collect these metrics and expose them to be scraped by a Prometheus server. To serve multiprocess metrics, disable Volley's metrics server and implement the Multiprocess collector according to the official [python client docs](https://github.com/prometheus/client_python).


## `volley_app_completions`
- Type: [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)
- Counter is incremented each time an application attempts to process a message. The labels depend on the outcome the application wrapped by `volley.Engine.stream_app`. The labels on the metric indicate the outcome of the application cycle.
- Labels:
    - `status`:
        - Values
            - `success` : application processed a message without raising an exception.
            - `failure` : application raised an exception to Volley.
