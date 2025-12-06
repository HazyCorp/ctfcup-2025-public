import aiohttp
import asyncio
import ssl
from datetime import datetime
from typing import Optional, Any

USER_AGENT = "checker"


def tprint(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = (0.5, 1.0, 2.0)  # Exponential backoff

# Exceptions that trigger retry
RETRIABLE_EXCEPTIONS = (
    aiohttp.ClientError,
    aiohttp.ServerTimeoutError,
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
)


def create_ssl_context():
    """Create SSL context that only allows TLS 1.3"""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_aiohttp_session(
    timeout: int = 10,
    connector: Optional[aiohttp.TCPConnector] = None
) -> aiohttp.ClientSession:
    """
    Create aiohttp session with TLS 1.3 and timeout.
    """
    if connector is None:
        ssl_context = create_ssl_context()
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            force_close=False,
            enable_cleanup_closed=True
        )
    
    timeout_config = aiohttp.ClientTimeout(
        total=timeout,
        connect=5,
        sock_read=timeout,
        sock_connect=5
    )
    
    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout_config,
        headers={"User-Agent": USER_AGENT}
    )


async def retry_request(
    coro_func,
    max_retries: int = MAX_RETRIES,
    retry_delays: tuple = RETRY_DELAYS
) -> Any:
    """
    Execute async function with retries on timeout/connection errors.
    
    Args:
        coro_func: Async function to execute (should be a callable that returns coroutine)
        max_retries: Maximum number of retry attempts
        retry_delays: List of delays between retries (exponential backoff)
    
    Returns:
        Result of the coroutine
    
    Raises:
        Last exception if all retries failed
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except RETRIABLE_EXCEPTIONS as e:
            last_exception = e
            
            if attempt < max_retries:
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                tprint(f"[RETRY] Attempt {attempt + 1}/{max_retries + 1} failed: {type(e).__name__}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                tprint(f"[RETRY] All {max_retries + 1} attempts failed: {type(e).__name__}")
    
    raise last_exception


class RetrySession:
    """
    Wrapper around aiohttp.ClientSession with automatic retries.
    """
    
    def __init__(self, session: aiohttp.ClientSession, max_retries: int = MAX_RETRIES):
        self._session = session
        self._max_retries = max_retries
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """GET request with retries."""
        async def do_request():
            response = await self._session.get(url, **kwargs)
            return response
        
        return await retry_request(do_request, self._max_retries)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """POST request with retries."""
        async def do_request():
            response = await self._session.post(url, **kwargs)
            return response
        
        return await retry_request(do_request, self._max_retries)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Access underlying session for advanced usage."""
        return self._session


def get_retry_session(timeout: int = 10, max_retries: int = MAX_RETRIES) -> RetrySession:
    """
    Create aiohttp session with automatic retries on timeouts.
    
    Usage:
        async with get_retry_session() as session:
            response = await session.get(url)
            # Automatically retries on timeout/connection errors
    """
    base_session = get_aiohttp_session(timeout=timeout)
    return RetrySession(base_session, max_retries=max_retries)
