import os
import threading

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
    start_http_server,
)

from volley.logging import logger

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn


def multiproc_collector() -> Starlette:

    async def app(request):
        prometheus_registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(prometheus_registry)
        data = generate_latest(prometheus_registry)
        headers = {
            "Content-type": CONTENT_TYPE_LATEST,
            "Content-length": str(len(data)),
        }
        return Response(data, media_type=CONTENT_TYPE_LATEST, headers=headers)


    return Starlette(routes=[
        Route('/metrics', app),
    ])


def serve_metrics(port: int) -> None:
    if os.getenv("PROMETHEUS_MULTIPROC_DIR") is not None:
        logger.info("Serving multi-process collector")
        server = multiproc_collector()
        t = threading.Thread(target=uvicorn.run, args=(server,), kwargs={'host': "0.0.0.0", "port": port})
        t.daemon = True
        t.start()
    else:
        start_http_server(port=port)
