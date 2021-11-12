import os
from datetime import datetime
from wsgiref.simple_server import make_server

import redis  # type: ignore
from prometheus_client import Gauge, make_wsgi_app
from sqlalchemy import text

from volley.connectors.pg_config import PG_SCHEMA, get_eng
from volley.queues import load_config

eng = get_eng()

all_queues = [x["value"] for x in load_config()["queues"] if x["type"] == "rsmq"]

g = Gauge("bundle_engine_queue_length", "Length of queues", ["queue_name", "queue_type"])
g_expired = Gauge("expired_messages", "Number of expired messages", ["queue_name", "queue_type"])


def get_publisher_queue_size() -> int:
    """returns total number of records in the publisher queue"""
    sql = f"""
        select count(*)
        from {PG_SCHEMA}.publisher
    """
    with eng.begin() as con:
        num_records: int = con.execute(text(sql)).fetchall()[0][0]
    return num_records


def get_expired_publisher() -> int:
    now = str(datetime.utcnow())
    sql = f"""
        select count(*)
        from {PG_SCHEMA}.publisher
        where timeout < '{now}'
    """
    with eng.begin() as con:
        num_records: int = con.execute(text(sql)).fetchall()[0][0]
    return num_records


def generate_metrics() -> None:
    r = redis.Redis(host=os.environ["REDIS_HOST"])
    for q in all_queues:
        _q = f"rsmq:{q}"
        size = r.zcard(_q)
        g.labels(queue_name=q, queue_type="rsmq").set(size)

    publisher_size = get_publisher_queue_size()
    g.labels(queue_name="publisher", queue_type="postgres").set(publisher_size)
    expired_size = get_expired_publisher()
    g_expired.labels(queue_name="publisher", queue_type="postgres").set(expired_size)


wsgi_app = make_wsgi_app()


def my_app(environ, start_fn):  # type: ignore
    generate_metrics()
    return wsgi_app(environ, start_fn)


server = make_server("", 8000, my_app)
server.serve_forever()
