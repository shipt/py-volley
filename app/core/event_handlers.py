import os
from typing import Callable

import rollbar
from fastapi import FastAPI
from loguru import logger

from app.core.config import DEFAULT_MODEL_PATH
from app.services.kafka_helper import KafkaProducer
from app.services.predict import HousePriceModel


def _init_rollbar(app: FastAPI) -> None:
    """Init rollbar module."""
    rollbar.init(
        os.getenv("ROLLBAR_TOKEN"),
        os.getenv("APP_ENV", "development"),
    )


def _startup_model(app: FastAPI) -> None:
    model_path = DEFAULT_MODEL_PATH
    model_instance = HousePriceModel(model_path)
    app.state.model = model_instance


def _startup_kafka_producer(app: FastAPI) -> None:
    app.state.kafka_producer = KafkaProducer()


def _shutdown_model(app: FastAPI) -> None:
    app.state.model = None


def _shutdown_kafka_producer(app: FastAPI) -> None:
    app.state.kafka_producer.kafka_flush()
    app.state.kafka_producer = None


def start_app_handler(app: FastAPI) -> Callable:
    def startup() -> None:
        logger.info("Running app start handler.")
        _init_rollbar(app)
        _startup_model(app)
        _startup_kafka_producer(app)

    return startup


def stop_app_handler(app: FastAPI) -> Callable:
    def shutdown() -> None:
        logger.info("Running app shutdown handler.")
        _shutdown_model(app)
        _shutdown_kafka_producer(app)

    return shutdown
