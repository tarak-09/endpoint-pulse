import asyncio
from monitor.config import MonitorConfig, GlobalSettings, EndpointConfig
from monitor.worker import WorkerPool
from aioresponses import aioresponses
import json

async def run():
    config = MonitorConfig(
        settings=GlobalSettings(
            pool_size=2,
            checks_per_endpoint=5,
            default_timeout=1.0,
            default_retries=1,
            default_retry_delay=0.1
        ),
        endpoints=[
            EndpointConfig(url="http://test.com/ok"),
            EndpointConfig(url="http://test.com/fail", retries=2, retry_delay=0.01),
        ]
    )
    with aioresponses() as m:
        m.get("http://test.com/ok", status=200, repeat=True)
        m.get("http://test.com/fail", status=500, repeat=True)
        pool = WorkerPool(config)
        results = await pool.run()
        print(json.dumps(results, indent=2))

asyncio.run(run())
