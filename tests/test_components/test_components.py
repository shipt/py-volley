from components.collector import main as collector
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.publisher import main as publisher
from components.triage import main as triage
from engine.data_models import BundleMessage, CollectorMessage
from engine.queues import available_queues


def test_vaid_(bundle_message: BundleMessage) -> None:
    queues = available_queues().queues
    valid_queue_names = [x for x, y in queues.items()]
    for component in [features, triage, fallback, optimizer]:
        b = bundle_message.copy()
        outputs = component.__wrapped__(b)
        for qname, message in outputs:
            assert isinstance(qname, str)
            assert isinstance(message, BundleMessage)
            assert qname in valid_queue_names


def test_collector(collector_message: CollectorMessage) -> None:
    f = collector.__wrapped__(collector_message.fallback_dict())
    o = collector.__wrapped__(collector_message.optimizer_dict())
    t = collector.__wrapped__(collector_message.triage_dict())
    for i in [f, o, t]:
        for _i in i:
            assert _i[0] == "publisher"
