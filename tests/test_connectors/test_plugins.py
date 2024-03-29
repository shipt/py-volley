from unittest.mock import MagicMock, patch

from volley.config import import_module_from_string
from volley.connectors.base import BaseConsumer, BaseProducer


@patch("example.plugins.my_plugin.Session")
@patch("example.plugins.my_plugin.get_eng")
def test_load_plugin(mock_eng: MagicMock, mock_sess: MagicMock) -> None:  # pylint: disable=W0613
    module_str = "example.plugins.my_plugin.MyPGConsumer"
    class_obj = import_module_from_string(module_str)
    assert issubclass(class_obj, BaseConsumer)

    pg_consumer = class_obj(queue_name="test-queue")
    assert isinstance(pg_consumer, BaseConsumer)

    module_str = "example.plugins.my_plugin.MyPGProducer"
    class_obj = import_module_from_string(module_str)
    assert issubclass(class_obj, BaseProducer)

    pg_producer = class_obj(queue_name="test-queue")
    assert isinstance(pg_producer, BaseProducer)
