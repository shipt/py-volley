from tasks.bundle_requests.tasks import BundleTasks


def test_main_func():
    assert "I processed a bundle request from Kafka!" in BundleTasks.main()
