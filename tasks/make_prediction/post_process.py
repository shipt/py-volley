import numpy as np

from data_models.prediction import HousePredictionResult


class PostProcess:
    def __init__(self) -> None:
        pass

    @staticmethod
    def format_prediction_result(prediction: np.ndarray) -> HousePredictionResult:
        """
        Format prediction result to Pydantic data model
        Args:
            prediction (np.ndarray): Output from models predict method
        Returns:
            HousePredictionResult: Expected data model returned to requestor
        """
        result_unit_factor = 100000
        result = prediction.tolist()
        human_readable_unit = result[0] * result_unit_factor
        hpp = HousePredictionResult(median_house_value=human_readable_unit)

        return hpp
