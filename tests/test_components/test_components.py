from components.collector import main as collector
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.triage import main as triage
from engine.data_models import BundleMessage
from engine.queues import available_queues

def test_collector_signatures(bundle_message: BundleMessage) -> None:
    queues = available_queues().queues
    valid_queue_names = [x for x,y in queues.items()]
    for component in [collector, fallback, features, optimizer, triage]:
        output = component.__wrapped__(bundle_message)
        for qname, message in output.items():
            assert isinstance(qname, str)
            assert isinstance(message, BundleMessage)
            assert qname in valid_queue_names
