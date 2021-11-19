from typing import Dict

from volley.queues import Queue, available_queues


def test_available_queues() -> None:
    all_queues: Dict[str, Queue] = available_queues()

    for qname, q in all_queues.items():
        assert isinstance(qname, str)
        assert isinstance(q, Queue)
