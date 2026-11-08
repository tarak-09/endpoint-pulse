from typing import List, Optional
import yaml
from pydantic import BaseModel, Field

class GlobalSettings(BaseModel):
    pool_size: int = Field(10, ge=1, description="Number of concurrent workers")
    checks_per_endpoint: int = Field(50, ge=1, description="Number of requests to send to each endpoint")
    default_timeout: float = Field(5.0, ge=0.1, description="Default timeout in seconds")
    default_retries: int = Field(3, ge=0, description="Default number of retries per check")
    default_retry_delay: float = Field(1.0, ge=0.0, description="Delay between retries in seconds")

class AssertionsConfig(BaseModel):
    jsonpath: Optional[str] = None
    regex: Optional[str] = None

class EndpointConfig(BaseModel):
    url: str
    method: str = "GET"
    timeout: Optional[float] = None
    retries: Optional[int] = None
    retry_delay: Optional[float] = None
    expected_status: int = 200
    assertions: Optional[AssertionsConfig] = None
    tls_expiration_threshold: Optional[int] = Field(None, description="Minimum number of days before TLS certificate expires")

class MonitorConfig(BaseModel):
    settings: GlobalSettings = Field(default_factory=GlobalSettings)
    endpoints: List[EndpointConfig]

def load_config(path: str) -> MonitorConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        data = {}
    return MonitorConfig(**data)
