import logging

import numpy as np

from data_models.payload import HousePredictionPayload, payload_to_list

FORMAT = "%(asctime)s %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger()


class PreProcess:
    def __init__(self) -> None:
        pass

    @staticmethod
    def fetch_features_from_feature_store():
        return "I pulled some features from the feature store!"

    @staticmethod
    def convert_to_np_array(payload: HousePredictionPayload) -> np.ndarray:
        """
        Converts incoming payload to numpy array

        Args:
            payload (HousePredictionPayload): [description]

        Returns:
            np.ndarray: Feature vector array
        """
        if payload is None:
            raise ValueError("Payload is None!")
        logger.info(f"Pre-processing payload: {payload.dict()}")
        result = np.asarray(payload_to_list(payload)).reshape(1, -1)

        return result
