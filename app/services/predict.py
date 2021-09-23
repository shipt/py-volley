import joblib
import numpy as np

from app.services.interface_model import IModel


class HousePriceModel(IModel):
    def __init__(self, path):
        self.path = path
        self._load_local_model()

    def _load_local_model(self):
        self.model = joblib.load(self.path)

    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Serialized models "predict" method

        Args:
            features (np.ndarray): Feature vector need to make prediction

        Returns:
            np.ndarray: Array of predicted feature results
        """
        prediction_result = self.model.predict(features)

        return prediction_result
