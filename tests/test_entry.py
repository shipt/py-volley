from unittest.mock import patch

import pytest

from main import run


def test_main() -> None:
    """just runs through the code in main.py. make sure it can execute"""
    for component in [
        "dummy_events",
        "dummy_consumer",
        "features",
        "triage",
        "optimizer",
        "fallback",
        "collector",
        "publisher",
    ]:
        with patch("sys.argv", ["program_name", component]):
            with patch(f"components.{component}.main"):
                run()


def test_notimpl_error() -> None:
    with patch("sys.argv", ["program_name", "I_DO_NOT_EXIST"]):
        with pytest.raises(NotImplementedError):
            run()
