import asyncio
import time
import aiohttp
from typing import List
import logging

from .config import MonitorConfig, EndpointConfig
from .metrics import EndpointMetrics

logger = logging.getLogger(__name__)

class WorkerPool:
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.metrics = {ep.url: EndpointMetrics(ep.url) for ep in config.endpoints}
        self.queue = asyncio.Queue()

    async def _fetch(self, session: aiohttp.ClientSession, endpoint: EndpointConfig) -> None:
        timeout_val = endpoint.timeout if endpoint.timeout is not None else self.config.settings.default_timeout
        retries = endpoint.retries if endpoint.retries is not None else self.config.settings.default_retries
        retry_delay = endpoint.retry_delay if endpoint.retry_delay is not None else self.config.settings.default_retry_delay
        
        timeout = aiohttp.ClientTimeout(total=timeout_val)
        
        for attempt in range(retries + 1):
            start_time = time.monotonic()
            try:
                async with session.request(endpoint.method, endpoint.url, timeout=timeout) as response:
                    latency = time.monotonic() - start_time
                    status = response.status
                    
                    if status == endpoint.expected_status:
                        self.metrics[endpoint.url].add_result(latency, status)
                        return
                    else:
                        error_msg = f"Unexpected status: {status}"
                        if attempt == retries:
                            self.metrics[endpoint.url].add_result(latency, status, error=error_msg)
                            return
            except asyncio.TimeoutError:
                if attempt == retries:
                    self.metrics[endpoint.url].add_result(time.monotonic() - start_time, 0, error="TimeoutError")
                    return
            except aiohttp.ClientError as e:
                if attempt == retries:
                    self.metrics[endpoint.url].add_result(time.monotonic() - start_time, 0, error=type(e).__name__)
                    return
            except Exception as e:
                if attempt == retries:
                    self.metrics[endpoint.url].add_result(time.monotonic() - start_time, 0, error=str(e))
                    return
            
            await asyncio.sleep(retry_delay)

    async def _worker(self, session: aiohttp.ClientSession):
        while True:
            try:
                endpoint = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            await self._fetch(session, endpoint)
            self.queue.task_done()

    async def run(self):
        for endpoint in self.config.endpoints:
            for _ in range(self.config.settings.checks_per_endpoint):
                self.queue.put_nowait(endpoint)
                
        async with aiohttp.ClientSession() as session:
            workers = [
                asyncio.create_task(self._worker(session))
                for _ in range(self.config.settings.pool_size)
            ]
            await asyncio.gather(*workers)
            
        return [m.calculate() for m in self.metrics.values()]
