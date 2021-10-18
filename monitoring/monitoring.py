import os
from typing import Any, Callable
from wsgiref.simple_server import make_server

import redis
from prometheus_client import Gauge, make_wsgi_app

from engine.queues import load_config

all_queues = [x["value"] for x in load_config()["queues"] if x["type"] == "rsmq" ]

g = Gauge('rsmq_queue_length', 'Length of queues', ['queue_name'])


def generate_metrics() -> None:
    r = redis.Redis(host=os.environ["REDIS_HOST"])
    for q in all_queues:
        _q = f"rsmq:{q}"
        size = r.zcard(_q)
        g.labels(q).set(size)

wsgi_app = make_wsgi_app()

def my_app(environ, start_fn):  # type: ignore
    generate_metrics()
    return wsgi_app(environ, start_fn)

server = make_server('', 8000, my_app)
server.serve_forever()