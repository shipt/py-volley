from starlette.config import Config

APP_VERSION = "0.0.1"
APP_NAME = "Machine Learning Prediction Example"
API_PREFIX = "/api"

config = Config(".env.example")

IS_DEBUG: bool = config("IS_DEBUG", cast=bool, default=False)
# DEFAULT_MODEL_PATH: str = config("DEFAULT_MODEL_PATH")
DEFAULT_MODEL_PATH: str = "./trained_model/lin_reg_california_housing_model.joblib"
