import logging

from volley.data_models import GenericMessage
from volley.engine import Engine
from volley.logging import logger

logging.basicConfig(level=logging.INFO)

eng = Engine(input_queue="output-topic", output_queues=[], yaml_config_path="./example/volley_config.yml")


@eng.stream_app
def main(input_message: GenericMessage) -> bool:
    """mimics an data consumer external to Volley"""

    logger.info(input_message.dict())

    return True


if __name__ == "__main__":
    main()
