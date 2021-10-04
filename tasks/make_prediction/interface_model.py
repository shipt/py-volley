from abc import ABC, abstractmethod


class IModel(ABC):
    @abstractmethod
    def predict():
        """
        Serialized model's .predict method
        """
