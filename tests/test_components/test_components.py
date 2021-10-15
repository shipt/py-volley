from components.collector import main as collector
from components.fallback import main as fallback
from components.features import main as features
from components.optimizer import main as optimizer
from components.triage import main as triage
from engine.data_models import BundleMessage


def test_collector_signatures(bundle_message: BundleMessage) -> None:
    for component in [collector, fallback, features, optimizer, triage]:
        output = component.__wrapped__(bundle_message)
        for qname, message in output.items():
            assert isinstance(qname, str)
            assert isinstance(message, BundleMessage)
