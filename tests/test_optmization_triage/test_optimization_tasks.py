from tasks.optimization_triage.tasks import OptimizationTasks


def test_main_func():
    assert "I triaged the optimizer!" in OptimizationTasks.main()
