import os
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Header
from starlette.requests import Request

from app.data_models.payload import HousePredictionPayload
from app.data_models.kafka_message import KafkaMessage
from app.data_models.prediction import HousePredictionResult
from app.services.kafka_helper import KafkaProducer
from app.services.post_process import PostProcess
from app.services.pre_process import PreProcess
from app.services.predict import HousePriceModel

router = APIRouter()


@router.post("/predict", response_model=HousePredictionResult, name="predict")
async def post_predict(
    request: Request,
    background_tasks: BackgroundTasks,
    block_data: HousePredictionPayload = None,
    x_request_id: Optional[str] = Header(None),
) -> HousePredictionResult:
    model: HousePriceModel = request.app.state.model
    kafka_producer: KafkaProducer = request.app.state.kafka_producer

    pre_processed_array: np.ndarray = PreProcess.convert_to_np_array(payload=block_data)
    predictions_array: np.ndarray = model.predict(pre_processed_array)
    post_processed_result: HousePredictionResult = PostProcess.format_prediction_result(predictions_array)

    kafka_message_payload = KafkaMessage(
        sent_at=str(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f000")) + "Z",
        prediction_id=x_request_id,
        predictor_name="ml-api",
        model_id="v1",
        features_dict=block_data.dict(),
        prediction_result=str(predictions_array),
        default_values_used=[],
    )

    background_tasks.add_task(
        kafka_producer.add_message_to_kafka,
        topic=os.getenv("PREDICTION_TOPIC"),
        value=kafka_message_payload.dict(),
    )

    return post_processed_result
