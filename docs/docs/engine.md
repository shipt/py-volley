# Application

The engine prepares a Python decorator that wraps a worker function to be run as a headless service.

## App Configuration

All configuration is passed in and initalized via the `Engine` class

```python hl_lines="3"
from volley.engine import Engine

app = Engine(...)
```

Engine attributes are described below:

::: volley.engine.Engine
