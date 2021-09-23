# import autodynatrace  # noqa: F401
import rollbar
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes.router import api_router
from app.core.config import API_PREFIX, APP_NAME, APP_VERSION, IS_DEBUG
from app.core.event_handlers import start_app_handler, stop_app_handler

instrumentator = Instrumentator()


async def rollbar_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        rollbar.report_exc_info()
        return Response("Internal server error", status_code=500)


def get_app() -> FastAPI:
    """FastAPI app controller"""
    fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)
    fast_app.middleware("http")(rollbar_middleware)
    fast_app.include_router(api_router, prefix=API_PREFIX)
    fast_app.add_event_handler("startup", start_app_handler(fast_app))
    fast_app.add_event_handler("shutdown", stop_app_handler(fast_app))
    instrumentator.instrument(fast_app).expose(fast_app, include_in_schema=False, should_gzip=False)
    return fast_app


app = get_app()
