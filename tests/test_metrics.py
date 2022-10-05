import time
import urllib.request
from unittest.mock import patch

import pytest

from volley.metrics import serve_metrics


def test_multiproc_metric_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """test the single process collector"""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp")
    port = 1234
    serve_metrics(port=port)
    time.sleep(0.5)
    resp = urllib.request.urlopen(f"http://0.0.0.0:{port}/metrics")
    assert resp.status == 200

    with patch("volley.metrics.multiproc_collector_server") as mock_http, patch(
        "volley.metrics.uvicorn.run"
    ) as mock_uvicorn:
        serve_metrics(port=port)
    mock_http.assert_called_once()
    mock_uvicorn.assert_called_once()


def test_metric_server() -> None:
    """test the single process collector"""
    port = 1235
    serve_metrics(port=port)
    time.sleep(0.5)
    resp = urllib.request.urlopen(f"http://0.0.0.0:{port}/metrics")
    assert resp.status == 200
    with patch("volley.metrics.start_http_server") as mock_http:
        serve_metrics(port=port)
    mock_http.assert_called_once()
