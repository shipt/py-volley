import os
import threading

import uvicorn
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
    start_http_server,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from volley.logging import logger


def multiproc_collector_server() -> Starlette:
    """Serves a multiprocess collector
    https://github.com/prometheus/client_python#multiprocess-mode-eg-gunicorn
    """

    async def app(request: Request) -> Response:  # pylint: disable=W0613
        prometheus_registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(prometheus_registry)
        data = generate_latest(prometheus_registry)
        headers = {
            "Content-type": CONTENT_TYPE_LATEST,
            "Content-length": str(len(data)),
        }
        return Response(data, media_type=CONTENT_TYPE_LATEST, headers=headers)

    return Starlette(
        routes=[
            Route("/metrics", app),
        ]
    )


def serve_metrics(port: int) -> None:
    """Serves the built-in prometheus webserver by default.
    Serves multiprocess collector when PROMETHEUS_MULTIPROC_DIR present in env vars.

    Both methods run the webserver on a daemon thread
    """
    if os.getenv("PROMETHEUS_MULTIPROC_DIR") is not None:
        logger.info("Serving multi-process collector")
        server = multiproc_collector_server()
        t = threading.Thread(target=uvicorn.run, args=(server,), kwargs={"host": "0.0.0.0", "port": port}, daemon=True)
        t.start()
    else:
        start_http_server(port=port)
