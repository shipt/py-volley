from abc import ABC, abstractmethod


class IModel(ABC):
    @abstractmethod
    def predict():
        """
        Saved/Serialized model predict method
        """
