# Metrics

Volley exports selected [Prometheus metrics](https://prometheus.io/docs/concepts/metric_types/) on all workers.

All metrics contain the label `volley_app` which is directly tied to the `app_name` parameter passed in when initializing `volley.engine.Engine()`.

## `messages_consumed_count` 
- [Counter](https://prometheus.io/docs/concepts/metric_types/#counter) 
- increments each time a message is consumed by the worker.
- Labels:
  - `status` : `success|fail`. If the worker consumes a message, but fails the corresponding produce operation, the message gets marked as a `fail`. Otherwise, it is a `success`.


## `messages_produced_count` 
- [Counter](https://prometheus.io/docs/concepts/metric_types/#counter)
- increments each time a message is produced
- Labels:
  - `source` : name of the queue the worker consumed from.
  - `destination` : name of the queue the message was produced to


## `process_time_seconds` 
- [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- observed the amount of time various processes take to run
- Labels:
  - `process_name` : name of the process that is tracked
    - Values:
      - `component` : time associated with the processing time for the function that Volley wraps. This is isolated to the logic in the user's function.
      - `cycle` : one full cycle of consume message, serialize, schema validation, component processing, and publishing to all outputs. `component` is a subset of `cycle`

## `redis_process_time_seconds` 
- [Summary](https://prometheus.io/docs/concepts/metric_types/#summary)
- similar to `process_time_seconds` but is isolated to the RSMQ connector.
- Labels:
  - `operation`: name of the operation
    - `read` : time to read a message from the queue
    - `delete` : time to delete a message from the queue
    - `write` : time to add a message to the queue


Applications can export their own metrics as well. Examples in the Prometheus official [python client](https://github.com/prometheus/client_python) are a great place to start. The Volley exporter will collect these metrics and expose them to be scraped by a Prometheus server.
