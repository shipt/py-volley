import pytest

from components.optimizer import main as optimizer

# TEST NULL MESSAGE
def test_optimizer_null_message(null_input_message: InputMessage) -> None:
    with pytest.raises(Exception):
        outputs = optimizer.__wrapped__(null_input_message)

# TEST INVALID INPUT
