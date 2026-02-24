"""
Async Connection Pooling and Resource Management
Optimized HTTP client with connection reuse
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp

from core.rate_limiter import RateLimitedClient, TokenBucket

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Connection pool configuration"""

    limit: int = 100
    limit_per_host: int = 10
    ttl_dns_cache: int = 300
    use_dns_cache: bool = True
    timeout: aiohttp.ClientTimeout = None

    def __post_init__(self):
        if self.timeout is None:
            self.timeout = aiohttp.ClientTimeout(total=60, connect=10)


class ConnectionPool:
    """
    Managed HTTP connection pool with rate limiting.
    Implements proper connection reuse and cleanup.
    """

    def __init__(self, config: PoolConfig = None):
        self.config = config or PoolConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._rate_limiter: Optional[TokenBucket] = None
        self._lock = asyncio.Lock()
        self._closed = True

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session with optimized connector"""
        self._connector = aiohttp.TCPConnector(
            limit=self.config.limit,
            limit_per_host=self.config.limit_per_host,
            ttl_dns_cache=self.config.ttl_dns_cache,
            use_dns_cache=self.config.use_dns_cache,
            enable_cleanup_closed=True,
            force_close=False,
        )

        # Global semaphore for concurrent request limiting
        self._semaphore = asyncio.Semaphore(self.config.limit)

        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=self.config.timeout,
            headers={
                "User-Agent": "Zen-AI-Pentest/1.0 (Security Scanner)",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
            },
        )

        self._closed = False
        return self._session

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create session"""
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    await self._create_session()
        return self._session

    @asynccontextmanager
    async def request(
        self, method: str, url: str, rate_limit: float = None, **kwargs
    ) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        """
        Make rate-limited HTTP request with connection pooling.

        Args:
            method: HTTP method
            url: Request URL
            rate_limit: Max requests per second (None = unlimited)
            **kwargs: Additional aiohttp request arguments
        """
        session = await self.get_session()

        # Apply rate limiting if configured
        if rate_limit and self._rate_limiter is None:
            self._rate_limiter = TokenBucket(rate=rate_limit, capacity=5)

        if self._rate_limiter:
            await self._rate_limiter.wait()

        # Limit concurrent requests
        async with self._semaphore:
            try:
                async with session.request(method, url, **kwargs) as response:
                    yield response
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error {method} {url}: {e}")
                raise

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Simple GET request"""
        async with self.request("GET", url, **kwargs) as response:
            return await response.text()

    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Simple POST request"""
        async with self.request("POST", url, **kwargs) as response:
            return await response.text()

    async def json_get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET request with JSON parsing"""
        async with self.request("GET", url, **kwargs) as response:
            return await response.json()

    async def close(self):
        """Close all connections properly"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
            if self._connector and not self._connector.closed:
                await self._connector.close()
            self._closed = True
            logger.debug("Connection pool closed")

    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @property
    def closed(self) -> bool:
        return self._closed


class SmartHTTPClient(RateLimitedClient):
    """
    HTTP client with circuit breaker, retries, and connection pooling.
    """

    def __init__(
        self,
        name: str,
        pool_config: PoolConfig = None,
        rate_config: Any = None,
        circuit_config: Any = None,
    ):
        super().__init__(name, rate_config, circuit_config)
        self.pool = ConnectionPool(pool_config)

    async def _do_request(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """Execute HTTP request with full error handling"""
        async with self.pool.request(method, url, **kwargs) as response:
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = await response.json()
            else:
                data = await response.text()

            return {
                "status": response.status,
                "headers": dict(response.headers),
                "data": data,
                "url": str(response.url),
            }

    async def close(self):
        await self.pool.close()
        await super().close()


class ParallelProcessor:
    """
    Execute tasks in parallel with semaphore-controlled concurrency.
    Prevents resource exhaustion during bulk operations.
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run(self, tasks: list, return_exceptions: bool = True) -> list:
        """
        Run tasks with controlled concurrency.

        Args:
            tasks: List of coroutines
            return_exceptions: If True, exceptions are returned instead of raised
        """

        async def bounded_task(task):
            async with self._semaphore:
                return await task

        # Create bounded tasks
        bounded = [bounded_task(t) for t in tasks]

        # Execute with exception handling
        return await asyncio.gather(
            *bounded, return_exceptions=return_exceptions
        )

    async def map(self, func: callable, items: list, *args, **kwargs) -> list:
        """
        Map function over items with controlled concurrency.

        Args:
            func: Async function to apply
            items: List of items to process
            *args, **kwargs: Additional arguments for func
        """
        tasks = [func(item, *args, **kwargs) for item in items]
        return await self.run(tasks)


# Global pool instance
_global_pool: Optional[ConnectionPool] = None


async def get_global_pool() -> ConnectionPool:
    """Get global connection pool"""
    global _global_pool
    if _global_pool is None:
        _global_pool = ConnectionPool()
    return _global_pool


async def close_global_pool():
    """Close global connection pool"""
    global _global_pool
    if _global_pool:
        await _global_pool.close()
        _global_pool = None


# Example usage patterns
async def example_bulk_requests(urls: list[str]):
    """Example: Bulk HTTP requests with connection pooling"""
    pool = ConnectionPool(PoolConfig(limit_per_host=5))

    processor = ParallelProcessor(max_concurrent=10)

    async def fetch(url):
        async with pool.request("GET", url) as response:
            return await response.text()

    results = await processor.map(fetch, urls)
    await pool.close()
    return results


async def example_with_circuit_breaker():
    """Example: HTTP client with circuit breaker"""
    from core.rate_limiter import CircuitBreakerConfig, RateLimitConfig

    client = SmartHTTPClient(
        name="api-client",
        pool_config=PoolConfig(limit_per_host=5),
        rate_config=RateLimitConfig(requests_per_second=2.0, burst_size=5),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=30.0
        ),
    )

    try:
        result = await client.request("GET", "https://api.example.com/data")
        print(result)
    finally:
        await client.close()
