from typing import Optional

from pydantic import BaseModel, Field


class KafkaMessage(BaseModel):
    sent_at: str = Field(example="2021-08-06 11:54:57.023438")
    prediction_id: Optional[str] = Field(example="82345")
    predictor_name: str = Field(example="shopper-demand")
    model_id: str = Field(example="v1")
    features_dict: dict = Field(example={"feature_1": 1.00, "feature_2": 2, "feature_3": 29.1, "feature_4": 1})
    prediction_result: str = Field(example="2.3987")
    default_values_used: list = Field(example=["feature_4"])
