import numpy as np
from loguru import logger

from app.core.messages import NO_VALID_PAYLOAD
from app.data_models.payload import HousePredictionPayload, payload_to_list


class PreProcess:
    def __init__(self) -> None:
        pass

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
            raise ValueError(NO_VALID_PAYLOAD.format(payload))
        logger.info(f"Pre-processing payload: {payload.dict()}")
        result = np.asarray(payload_to_list(payload)).reshape(1, -1)

        return result
