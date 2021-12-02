from volley.data_models import ComponentMessage
from volley.engine import Engine
from volley.logging import logger

eng = Engine(input_queue="output-topic", output_queues=[], yaml_config_path="./example/volley_config.yml")


@eng.stream_app
def main(input_message: ComponentMessage) -> None:
    """mimics an data consumer external to Volley"""

    logger.info(input_message.dict())

    return None


if __name__ == "__main__":
    main()
