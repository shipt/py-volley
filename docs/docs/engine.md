# Engine

The engine is a Python decorator that wraps a Python worker and runs as headless services.

On initialization:
- setup connections to the queues using the connectors specified by the components inputs and outputs
- determines the data schema required by the component


At runtime:
- The application runs a main loop which consists of:
  - polling the specified `queue` for new messages via a `connector`
  - `connector` passes message through `serialization`
  - `serialization` passes the message to a specified `validator`
  - messages enters the client provides Python function.

This process is executed in reverse order on the message returned by the client Python function.

Messages that fail either `serialization` or `validation` are routed to a dead-letter-queue, if specified.