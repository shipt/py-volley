import pytest

from tasks.bundle_requests.tasks import BundleTasks
from tasks.optimization_triage.tasks import OptimizationTasks


@pytest.fixture()
def bundle_worker():
    yield BundleTasks


@pytest.fixture()
def optimization_worker():
    yield OptimizationTasks
