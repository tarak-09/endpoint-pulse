import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from monitor.worker import WorkerPool
from monitor.config import MonitorConfig, GlobalSettings, EndpointConfig

@pytest.mark.asyncio
async def test_worker_tls_valid():
    config = MonitorConfig(
        settings=GlobalSettings(pool_size=1, checks_per_endpoint=1, default_retries=0),
        endpoints=[EndpointConfig(url="https://example.com", tls_expiration_threshold=10)]
    )
    pool = WorkerPool(config)

    mock_response = MagicMock(); mock_response.text = AsyncMock()
    mock_response.status = 200
    mock_conn = MagicMock()
    mock_transport = MagicMock()
    future_time_str = "Dec 30 19:09:53 2030 GMT"
    mock_transport.get_extra_info.return_value = {"notAfter": future_time_str}
    mock_conn.transport = mock_transport
    mock_response.connection = mock_conn

    mock_request_ctx = MagicMock()
    mock_request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_request_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.request.return_value = mock_request_ctx

    with patch("monitor.worker.time.monotonic", return_value=0):
        await pool._fetch(mock_session, config.endpoints[0])

    res = pool.metrics["https://example.com"].calculate()
    assert res["successes"] == 1
    assert res["failures"] == 0
    assert "tls_status" in res
    assert res["tls_status"]["valid"] is True
    assert res["tls_status"]["days_remaining"] > 10

@pytest.mark.asyncio
async def test_worker_tls_invalid():
    config = MonitorConfig(
        settings=GlobalSettings(pool_size=1, checks_per_endpoint=1, default_retries=0),
        endpoints=[EndpointConfig(url="https://example.com", tls_expiration_threshold=10)]
    )
    pool = WorkerPool(config)

    mock_response = MagicMock(); mock_response.text = AsyncMock()
    mock_response.status = 200
    mock_conn = MagicMock()
    mock_transport = MagicMock()
    past_time_str = "Dec 30 19:09:53 2020 GMT"
    mock_transport.get_extra_info.return_value = {"notAfter": past_time_str}
    mock_conn.transport = mock_transport
    mock_response.connection = mock_conn

    mock_request_ctx = MagicMock()
    mock_request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_request_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.request.return_value = mock_request_ctx

    with patch("monitor.worker.time.monotonic", return_value=0):
        await pool._fetch(mock_session, config.endpoints[0])

    res = pool.metrics["https://example.com"].calculate()
    assert res["successes"] == 0
    assert res["failures"] == 1
    assert "tls_status" in res
    assert res["tls_status"]["valid"] is False
    assert res["tls_status"]["days_remaining"] < 0
    assert "TLS certificate expires" in list(res["errors"].keys())[0]

