# Endpoint Health Monitor

A concurrent endpoint health monitor built with Python, `asyncio`, and `aiohttp`.

## Purpose
This tool allows you to monitor the health and latency of a list of HTTP endpoints. It operates using an asynchronous worker pool, making it extremely efficient. It supports configurable timeouts, retry policies, response payload assertions (JSONPath and regex), and generates a structured JSON report containing latency percentiles (p50, p95, p99) and status summaries.

## Installation

The project uses `uv` for dependency management.

1. Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone this repository and navigate to the project root.

3. Sync dependencies (this will automatically create a virtual environment):
```bash
uv sync
```

## Configuration
The tool uses a YAML configuration file. See `example.yaml` for a working example.

```yaml
settings:
  pool_size: 10               # Number of concurrent workers
  checks_per_endpoint: 50     # Number of requests to send to each endpoint
  default_timeout: 5.0        # Default timeout in seconds
  default_retries: 3          # Default number of retries per check
  default_retry_delay: 1.0    # Delay between retries in seconds

endpoints:
  - url: https://httpbin.org/status/200
    method: GET
  - url: https://httpbin.org/delay/2
    method: GET
    timeout: 3.0
    retries: 1
  - url: https://httpbin.org/json
    method: GET
    assertions:
      jsonpath: "$.slideshow.author"
  - url: https://httpbin.org/html
    method: GET
    assertions:
      regex: "<h1>.*</h1>"
  - url: https://example.com
    tls_expiration_threshold: 30 # Check if TLS cert expires in < 30 days
```

## Usage

Run the tool using `uv`. You can optionally specify a SQLite database to save the run metrics for historical tracking:

```bash
uv run monitor -c example.yaml
# Or, to save metrics:
uv run monitor -c example.yaml --db metrics.db
```

### Viewing History
If you have saved metrics using the `--db` flag, you can view a history of latency trends and failure rates using the `history` subcommand:

```bash
uv run monitor history --db metrics.db
```

This will render a text-based table like:
```text
Timestamp              | URL                            | Reqs  | Fail %  | p50(ms)  | p95(ms)  | p99(ms) 
---------------------------------------------------------------------------------------------------------
2024-01-01 12:00:00    | https://httpbin.org/status/200 | 50    | 0.0%    | 115.42   | 138.91   | 150.12  
```

### Example Output (JSON)
```json
[
  {
    "url": "https://httpbin.org/status/200",
    "total_requests": 50,
    "successes": 50,
    "failures": 0,
    "latencies": {
      "p50_ms": 115.42,
      "p95_ms": 138.91,
      "p99_ms": 150.12
    },
    "status_codes": {
      "200": 50
    },
    "errors": {},
    "tls_status": {
      "valid": true,
      "days_remaining": 45.2
    }
  },
  {
    "url": "https://httpbin.org/status/500",
    "total_requests": 50,
    "successes": 0,
    "failures": 50,
    "latencies": {
      "p50_ms": 0.0,
      "p95_ms": 0.0,
      "p99_ms": 0.0
    },
    "status_codes": {},
    "errors": {
      "Unexpected status: 500": 50
    }
  }
]
```

## Running Tests

Tests are written using `pytest`. You can run them via:
```bash
uv run pytest
```
