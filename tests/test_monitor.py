import pytest
import asyncio
from aiohttp import web
from monitor.metrics import EndpointMetrics
from monitor.worker import WorkerPool
from monitor.config import MonitorConfig, GlobalSettings, EndpointConfig, AssertionsConfig

async def ok_handler(request):
    return web.Response(status=200)

async def fail_handler(request):
    return web.Response(status=500)

async def json_handler(request):
    return web.json_response({"status": "success", "data": {"id": 123}})

async def text_handler(request):
    return web.Response(text="Hello World 2026")

@pytest.mark.asyncio
async def test_worker_pool_success():
    app = web.Application()
    app.router.add_get('/ok', ok_handler)
    app.router.add_get('/fail', fail_handler)
    app.router.add_get('/json', json_handler)
    app.router.add_get('/text', text_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 0)
    await site.start()

    port = runner.addresses[0][1]
    base_url = f"http://localhost:{port}"

    config = MonitorConfig(
        settings=GlobalSettings(
            pool_size=2,
            checks_per_endpoint=2,
            default_timeout=1.0,
            default_retries=0,
            default_retry_delay=0.1
        ),
        endpoints=[
            EndpointConfig(url=f"{base_url}/ok"),
            EndpointConfig(url=f"{base_url}/fail"),
            EndpointConfig(
                url=f"{base_url}/json",
                assertions=AssertionsConfig(jsonpath="$.data.id")
            ),
            EndpointConfig(
                url=f"{base_url}/text",
                assertions=AssertionsConfig(regex="Hello World \\d{4}")
            ),
            EndpointConfig(
                url=f"{base_url}/json?fail_jsonpath=1",
                assertions=AssertionsConfig(jsonpath="$.data.invalid")
            ),
            EndpointConfig(
                url=f"{base_url}/text?fail_regex=1",
                assertions=AssertionsConfig(regex="Goodbye")
            ),
        ]
    )

    pool = WorkerPool(config)
    results = await pool.run()

    await runner.cleanup()

    assert len(results) == 6

    ok_result = next(r for r in results if r["url"] == f"{base_url}/ok")
    assert ok_result["successes"] == 2
    assert ok_result["failures"] == 0
    assert "p50_ms" in ok_result["latencies"]

    fail_result = next(r for r in results if r["url"] == f"{base_url}/fail")
    assert fail_result["successes"] == 0
    assert fail_result["failures"] == 2
    assert fail_result["errors"] == {"Unexpected status: 500": 2}

    json_result = next(r for r in results if r["url"] == f"{base_url}/json")
    assert json_result["successes"] == 2

    text_result = next(r for r in results if r["url"] == f"{base_url}/text")
    assert text_result["successes"] == 2

    json_fail_result = next(r for r in results if r["url"] == f"{base_url}/json?fail_jsonpath=1")
    assert json_fail_result["successes"] == 0
    assert json_fail_result["failures"] == 2
    assert json_fail_result["errors"] == {"JSONPath assertion failed: $.data.invalid": 2}

    text_fail_result = next(r for r in results if r["url"] == f"{base_url}/text?fail_regex=1")
    assert text_fail_result["successes"] == 0
    assert text_fail_result["failures"] == 2
    assert text_fail_result["errors"] == {"Regex assertion failed: Goodbye": 2}



def test_metrics_calculation():
    metrics = EndpointMetrics("http://test.com")
    metrics.add_result(0.1, 200)
    metrics.add_result(0.2, 200)
    metrics.add_result(0.3, 200)
    metrics.add_result(0.4, 200)
    
    result = metrics.calculate()
    assert result["successes"] == 4
    # With 4 points: p50 should be ~0.25, p95 should be ~0.385, p99 should be ~0.397
    assert 200 <= result["latencies"]["p50_ms"] <= 300

def test_db_persistence(tmp_path):
    from monitor.db import init_db, save_metrics, get_history
    db_file = tmp_path / "test.db"
    
    conn = init_db(str(db_file))
    
    results = [
        {
            "url": "http://example.com",
            "total_requests": 10,
            "successes": 8,
            "failures": 2,
            "latencies": {
                "p50_ms": 100.0,
                "p95_ms": 150.0,
                "p99_ms": 200.0
            }
        }
    ]
    
    save_metrics(conn, results)
    conn.close()
    
    rows = get_history(str(db_file))
    assert len(rows) == 1
    # timestamp, url, total_requests, failures, p50_ms, p95_ms, p99_ms
    assert rows[0][1] == "http://example.com"
    assert rows[0][2] == 10
    assert rows[0][3] == 2
    assert rows[0][4] == 100.0
