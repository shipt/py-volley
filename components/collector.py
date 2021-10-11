import os

from engine.component import bundle_engine
from engine.data_models import BundleMessage

INPUT_QUEUE = os.environ["INPUT_QUEUE"]
OUTPUT_QUEUE = os.environ["OUTPUT_QUEUE"]


@bundle_engine(input_type="rsmq", output_type="kafka")
def main(message: BundleMessage) -> BundleMessage:
    message.message["collector"] = "collected"
    return message
