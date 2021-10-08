import os

from components.base import Component
from unittest.mock import patch

@patch("components.base.RedisSMQ")
def test_base_component(mocked_rsmq) -> None:
    input_q = os.environ["INPUT_QUEUE"]
    output_q = os.environ["OUTPUT_QUEUE"]

    in_q = Component(qname=input_q)
    out_q = Component(qname=output_q)


