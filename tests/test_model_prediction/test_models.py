import pytest

from data_models.payload import HousePredictionPayload
from data_models.prediction import HousePredictionResult
from tasks.make_prediction.post_process import PostProcess
from tasks.make_prediction.pre_process import PreProcess
from tasks.make_prediction.predict import HousePriceModel


def test_prediction() -> None:
    model_path = "./trained_model/lin_reg_california_housing_model.joblib"
    model_name = "test-model"
    model_version = "test-version"
    hpp = HousePredictionPayload.parse_obj(
        {
            "median_income_in_block": 8.3252,
            "median_house_age_in_block": 41,
            "average_rooms": 6,
            "average_bedrooms": 1,
            "population_per_block": 322,
            "average_house_occupancy": 2.55,
            "block_latitude": 37.88,
            "block_longitude": -122.23,
        }
    )

    hpm = HousePriceModel(path=model_path, name=model_name, version=model_version)
    pre_processed_array = PreProcess.convert_to_np_array(payload=hpp)
    result = hpm.predict(pre_processed_array)
    post_processed_result = PostProcess.format_prediction_result(result)
    assert isinstance(post_processed_result, HousePredictionResult)


def test_no_payload() -> None:
    with pytest.raises(ValueError):
        pre_processed_array = PreProcess.convert_to_np_array(
            payload=None
        )  # type:ignore
        assert pre_processed_array
