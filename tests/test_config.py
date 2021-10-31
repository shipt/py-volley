from engine.queues import Queue, available_queues


def test_available_queues() -> None:
    all_queues = available_queues()

    for qname, q in all_queues.queues.items():
        assert isinstance(qname, str)
        assert isinstance(q, Queue)
