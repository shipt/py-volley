from engine.queues import available_queues, Queue


def test_available_queues() -> None:
    all_queues = available_queues()

    for qname, Q in all_queues.queues.items():
        assert isinstance(qname, str)
        assert isinstance(Q, Queue)
