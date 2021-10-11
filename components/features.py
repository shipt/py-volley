from engine.component import bundle_engine
from engine.data_models import BundleMessage


@bundle_engine(input_type="kafka", output_type="rsmq")
def main(message: BundleMessage) -> BundleMessage:
    message.message["features"] = {"feature": "random"}
    return message
