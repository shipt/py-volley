import os
from wsgiref.simple_server import make_server

import redis  # type: ignore
from prometheus_client import Gauge, make_wsgi_app
from sqlalchemy import text

from engine.queues import load_config
from engine.stateful.pg_config import PG_SCHEMA, get_eng

eng = get_eng()

all_queues = [x["value"] for x in load_config()["queues"] if x["type"] == "rsmq"]

g_redis = Gauge("rsmq_queue_length", "Length of queues", ["queue_name"])
g_postgres = Gauge("psql_queue_length", "Length of queues", ["queue_name"])


def get_publisher_queue_size() -> int:
    sql = f"""
        select count(*)
        from {PG_SCHEMA}.publisher
    """
    with eng.begin() as con:
        num_records: int = con.execute(text(sql)).fetchall()[0][0]
    return num_records


def generate_metrics() -> None:
    r = redis.Redis(host=os.environ["REDIS_HOST"])
    for q in all_queues:
        _q = f"rsmq:{q}"
        size = r.zcard(_q)
        g_redis.labels(q).set(size)

    publisher_size = get_publisher_queue_size()
    g_postgres.labels("publisher").set(publisher_size)


wsgi_app = make_wsgi_app()


def my_app(environ, start_fn):  # type: ignore
    generate_metrics()
    return wsgi_app(environ, start_fn)


server = make_server("", 8000, my_app)
server.serve_forever()
