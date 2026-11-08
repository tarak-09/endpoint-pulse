import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from monitor.worker import WorkerPool
from monitor.config import MonitorConfig, GlobalSettings, EndpointConfig

async def main():
    config = MonitorConfig(
        settings=GlobalSettings(pool_size=1, checks_per_endpoint=1, default_retries=0),
        endpoints=[EndpointConfig(url="https://example.com", tls_expiration_threshold=10)]
    )
    pool = WorkerPool(config)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_conn = MagicMock()
    mock_transport = MagicMock()
    mock_transport.get_extra_info.return_value = {"notAfter": "Dec 30 19:09:53 2030 GMT"}
    mock_conn.transport = mock_transport
    mock_response.connection = mock_conn

    mock_request_ctx = AsyncMock()
    mock_request_ctx.__aenter__.return_value = mock_response

    mock_session = AsyncMock()
    mock_session.request.return_value = mock_request_ctx
    
    await pool._fetch(mock_session, config.endpoints[0])
    print(pool.metrics["https://example.com"].calculate())

asyncio.run(main())
