from typing import List, Dict, Any
import statistics

class EndpointMetrics:
    def __init__(self, url: str):
        self.url = url
        self.latencies: List[float] = []
        self.successes = 0
        self.failures = 0
        self.status_codes: Dict[int, int] = {}
        self.errors: Dict[str, int] = {}
        self.tls_status = None

    def set_tls_status(self, valid: bool, days_remaining: float, error: str = None):
        self.tls_status = {
            "valid": valid,
            "days_remaining": days_remaining,
        }
        if error:
            self.tls_status["error"] = error

    def add_result(self, latency: float, status_code: int, error: str = None):
        if error:
            self.failures += 1
            self.errors[error] = self.errors.get(error, 0) + 1
        else:
            self.successes += 1
            self.latencies.append(latency)
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

    def calculate(self) -> Dict[str, Any]:
        p50 = p95 = p99 = 0.0
        
        if self.latencies:
            sorted_lat = sorted(self.latencies)
            def percentile(p):
                if not sorted_lat:
                    return 0.0
                k = (len(sorted_lat) - 1) * p
                f = int(k)
                c = f + 1
                if c >= len(sorted_lat):
                    return sorted_lat[-1]
                return sorted_lat[f] + (k - f) * (sorted_lat[c] - sorted_lat[f])
            
            p50 = percentile(0.50)
            p95 = percentile(0.95)
            p99 = percentile(0.99)
            
        result = {
            "url": self.url,
            "total_requests": self.successes + self.failures,
            "successes": self.successes,
            "failures": self.failures,
            "latencies": {
                "p50_ms": round(p50 * 1000, 2),
                "p95_ms": round(p95 * 1000, 2),
                "p99_ms": round(p99 * 1000, 2),
            },
            "status_codes": self.status_codes,
            "errors": self.errors
        }
        if self.tls_status is not None:
            result["tls_status"] = self.tls_status
        return result
