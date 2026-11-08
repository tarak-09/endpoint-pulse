import asyncio
import aiohttp
from src.monitor.config import EndpointConfig, MonitorConfig, GlobalSettings
from src.monitor.worker import WorkerPool

async def main():
    config = MonitorConfig(
        settings=GlobalSettings(pool_size=1, checks_per_endpoint=1),
        endpoints=[EndpointConfig(url="https://google.com", tls_expiration_threshold=30)]
    )
    pool = WorkerPool(config)
    res = await pool.run()
    import json
    print(json.dumps(res, indent=2))

asyncio.run(main())
