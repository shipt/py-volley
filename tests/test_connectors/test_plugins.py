from unittest.mock import MagicMock, patch

from volley.config import import_module_from_string
from volley.connectors.base import Consumer, Producer


@patch("example.plugins.my_plugin.Session")
@patch("example.plugins.my_plugin.get_eng")
def test_load_plugin(mock_eng: MagicMock, mock_sess: MagicMock) -> None:
    module_str = "example.plugins.my_plugin.MyPGConsumer"
    class_obj = import_module_from_string(module_str)
    assert issubclass(class_obj, Consumer)

    pg_producer = class_obj(queue_name="test-queue")
    assert isinstance(pg_producer, Consumer)

    module_str = "example.plugins.my_plugin.MyPGProducer"
    class_obj = import_module_from_string(module_str)
    assert issubclass(class_obj, Producer)

    pg_producer = class_obj(queue_name="test-queue")
    assert isinstance(pg_producer, Producer)
