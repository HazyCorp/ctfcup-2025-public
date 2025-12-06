import requests
import functools
import ssl
import urllib3
from requests.adapters import HTTPAdapter, Retry
from urllib3.util.ssl_ import create_urllib3_context

USER_AGENT = lambda: "checker"

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TLS13HTTPAdapter(HTTPAdapter):
    """HTTPAdapter that forces TLS 1.3 only"""

    def init_poolmanager(self, *args, **kwargs):
        # Create SSL context that only allows TLS 1.3
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def requests_with_retries(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(400, 404, 500, 502),
    default_timeout=5,
    session=None,
):
    requests.adapters.DEFAULT_POOL_TIMEOUT = default_timeout
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = TLS13HTTPAdapter(max_retries=retry)
    session.headers.update({"User-Agent": USER_AGENT()})
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    # Disable SSL verification for self-signed certificates
    session.verify = False

    patch_methods_with_default_timeout(session, default_timeout)

    return session


def patch_methods_with_default_timeout(session, timeout):
    for method in ('get', 'options', 'head', 'post', 'put', 'patch', 'delete'):
        setattr(session, method, functools.partial(getattr(session, method), timeout=timeout))
