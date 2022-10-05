import time
import urllib.request

import pytest
from prometheus_client import Counter

from volley.metrics import serve_metrics

c = Counter("test_counter", "random description")


def test_multiproc_metric_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """test the single process collector"""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp")
    port = 1234
    serve_metrics(port=port)
    time.sleep(0.5)
    resp = urllib.request.urlopen(f"http://0.0.0.0:{port}/metrics")
    assert resp.status == 200
    assert "Multiprocess" in resp.read().decode("utf-8")


def test_metric_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """test the single process collector"""
    port = 1235
    serve_metrics(port=port)
    time.sleep(0.5)
    resp = urllib.request.urlopen(f"http://0.0.0.0:{port}/metrics")
    assert resp.status == 200
    assert "Multiprocess" not in resp.read().decode("utf-8")
