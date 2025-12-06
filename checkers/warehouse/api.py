"""
API client for TI Server
"""

import requests
from typing import Optional, Tuple, List, Dict
from request_utils import requests_with_retries


class TIServerAPI:
    """Client for interacting with TI Server API"""

    def __init__(self, host: str, timeout: int = 10, path_prefix: str = ""):
        self.base_url = f"https://{host}"
        self.path_prefix = path_prefix
        self.timeout = timeout
        self.session = requests_with_retries(default_timeout=timeout)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{self.path_prefix}{path}"
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)

    def create_feed(self, name: str, description: str, is_public: bool) -> Tuple[str, Optional[str]]:
        """
        Create a new feed

        Returns:
            Tuple of (feed_id, api_key)
        """
        data = {
            "name": name,
            "description": description,
            "is_public": is_public
        }

        resp = self._request("POST", "/feeds", json=data)
        resp.raise_for_status()

        feed = resp.json()
        feed_id = feed["id"]
        api_key = feed.get("api_key") if not is_public else None

        return feed_id, api_key

    def get_feed(self, feed_id: str, api_key: Optional[str] = None) -> Dict:
        """Get feed by ID"""
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        resp = self._request("GET", f"/feeds/{feed_id}", headers=headers)
        resp.raise_for_status()

        return resp.json()

    def get_feeds(self, is_public: Optional[bool] = None, limit: int = 10, offset: int = 0) -> Dict:
        """Get feeds with pagination"""
        params = {"limit": limit, "offset": offset}
        if is_public is True:
            params["is_public"] = "true"
        elif is_public is False:
            params["is_public"] = "false"
        resp = self._request("GET", "/feeds", params=params)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return {
                "feeds": data,
                "total": len(data),
                "limit": limit,
                "offset": offset
            }
        # Server returns 'items' field, normalize to 'feeds'
        if "items" in data:
            data["feeds"] = data.pop("items")
        return data

    def get_public_feeds(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        return self.get_feeds(is_public=True, limit=limit, offset=offset).get("feeds", [])

    def get_private_feeds(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        return self.get_feeds(is_public=False, limit=limit, offset=offset).get("feeds", [])

    def get_all_feeds(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        return self.get_feeds(is_public=None, limit=limit, offset=offset).get("feeds", [])

    def add_ioc(self, feed_id: str, ioc_type: str, value: str,
                severity: str = "medium", description: str = "", api_key: Optional[str] = None) -> str:
        """
        Add IOC to feed

        Returns:
            IOC ID
        """
        data = {
            "type": ioc_type,
            "value": value,
            "severity": severity,
            "description": description
        }

        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        resp = self._request("POST", f"/feeds/{feed_id}/iocs", json=data, headers=headers)
        resp.raise_for_status()

        ioc = resp.json()
        return ioc["id"]

    def get_iocs(self, feed_id: str, api_key: Optional[str] = None) -> List[Dict]:
        """Get all IOCs from feed"""
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key

        resp = self._request("GET", f"/feeds/{feed_id}/iocs", headers=headers)
        resp.raise_for_status()

        return resp.json()


class WarehouseAPI:
    """Client for interacting with Warehouse service"""

    def __init__(self, host: str, timeout: int = 10,
                 warehouse_prefix: str = "", auth_prefix: str = ""):
        self.warehouse_base = f"https://{host}{warehouse_prefix}"
        self.auth_base = f"https://{host}{auth_prefix}"
        self.timeout = timeout
        self.session = requests_with_retries(default_timeout=timeout)

    def _request(self, base_url: str, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{base_url}{path}"
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)

    def register_user(self, username: str, email: str, password: str) -> Dict:
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        resp = self._request(self.auth_base, "POST", "/auth/register", json=data)
        resp.raise_for_status()
        return resp.json()

    def login(self, username: str, password: str) -> str:
        data = {
            "username": username,
            "password": password
        }
        resp = self._request(self.auth_base, "POST", "/auth/login", json=data)
        resp.raise_for_status()
        payload = resp.json()
        token = payload.get("token")
        if not token:
            raise ValueError("No token in login response")
        return token

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def create_realm(self, token: str, name: str, description: str) -> Dict:
        data = {"name": name, "description": description}
        resp = self._request(self.warehouse_base, "POST", "/api/realms", json=data, headers=self._auth_headers(token))
        resp.raise_for_status()
        return resp.json()

    def get_realms(self, token: str) -> List[Dict]:
        resp = self._request(self.warehouse_base, "GET", "/api/realms", headers=self._auth_headers(token))
        resp.raise_for_status()
        return resp.json()

    def create_asset(self, token: str, realm_id: str, name: str, asset_type: str, description: str,
                     owner_user_id: Optional[str] = None) -> Dict:
        data = {
            "name": name,
            "asset_type": asset_type,
            "description": description
        }
        if owner_user_id:
            data["owner_user_id"] = owner_user_id
        resp = self._request(
            self.warehouse_base,
            "POST",
            f"/api/realms/{realm_id}/assets",
            json=data,
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def get_realm_assets(self, token: str, realm_id: str) -> Dict:
        resp = self._request(
            self.warehouse_base,
            "GET",
            f"/api/realms/{realm_id}/assets",
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def get_asset(self, token: str, asset_id: str) -> Dict:
        resp = self._request(
            self.warehouse_base,
            "GET",
            f"/api/assets/{asset_id}",
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def add_user_to_realm(self, token: str, realm_id: str, user_id: str, role: str) -> Dict:
        data = {"user_id": user_id, "role": role}
        resp = self._request(
            self.warehouse_base,
            "POST",
            f"/api/realms/{realm_id}/users",
            json=data,
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def create_gateway_protection(
        self,
        token: str,
        realm_id: str,
        slug: str,
        require_auth: bool,
        ti_mode: str,
        rate_limit_enabled: bool,
        rate_limit_requests: int,
        rate_limit_window_sec: int,
        log_retention_minutes: int
    ) -> Dict:
        data = {
            "slug": slug,
            "require_auth": require_auth,
            "ti_mode": ti_mode,
            "rate_limit_enabled": rate_limit_enabled,
            "rate_limit_requests": rate_limit_requests,
            "rate_limit_window_sec": rate_limit_window_sec,
            "log_retention_minutes": log_retention_minutes
        }

        resp = self._request(
            self.warehouse_base,
            "POST",
            f"/api/realms/{realm_id}/gateway-protection",
            json=data,
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def search_users(self, token: str, query: str, limit: int = 10) -> List[Dict]:
        """Search users by username substring"""
        params = {"query": query, "limit": limit}
        resp = self._request(
            self.warehouse_base,
            "GET",
            "/api/users/search",
            params=params,
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("users", [])


class AuthServerAPI:
    """Client for interacting with Auth Server"""

    def __init__(self, host: str, timeout: int = 10, path_prefix: str = ""):
        self.base_url = f"https://{host}"
        self.path_prefix = path_prefix
        self.timeout = timeout
        self.session = requests_with_retries(default_timeout=timeout)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{self.path_prefix}{path}"
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)

    def register_user(self, username: str, email: str, password: str) -> Dict:
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        resp = self._request("POST", "/auth/register", json=data)
        resp.raise_for_status()
        return resp.json()

    def login(self, username: str, password: str) -> Dict:
        data = {
            "username": username,
            "password": password
        }
        resp = self._request("POST", "/auth/login", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_profile(self, token: str) -> Dict:
        headers = {"Authorization": f"Bearer {token}"}
        resp = self._request("GET", "/auth/profile", headers=headers)
        resp.raise_for_status()
        return resp.json()

    def logout(self, token: str) -> Dict:
        headers = {"Authorization": f"Bearer {token}"}
        resp = self._request("POST", "/auth/logout", headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_public_key(self) -> Dict:
        resp = self._request("GET", "/auth/public-key")
        resp.raise_for_status()
        return resp.json()

    def list_users(self, token: str, limit: int = 10, offset: int = 0) -> Dict:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"limit": limit, "offset": offset}
        resp = self._request("GET", "/users", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()


class GatewayAPI:
    """Client for interacting with Gateway service"""

    def __init__(self, host: str, timeout: int = 10, path_prefix: str = ""):
        self.base_url = f"https://{host}"
        self.path_prefix = path_prefix
        self.timeout = timeout
        self.session = requests_with_retries(default_timeout=timeout)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{self.path_prefix}{path}"
        kwargs.setdefault('timeout', self.timeout)
        return self.session.request(method, url, **kwargs)

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def login(self, username: str, password: str) -> Dict:
        data = {
            "username": username,
            "password": password
        }
        resp = self._request("POST", "/auth/login", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_virtual_service(self, token: str, vs_id: str) -> Dict:
        resp = self._request(
            "GET",
            f"/api/virtual-services/{vs_id}",
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def get_vs_feeds(self, token: str, vs_id: str) -> List[Dict]:
        resp = self._request(
            "GET",
            f"/api/virtual-services/{vs_id}/ti-feeds",
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("ti_feeds", [])

    def attach_ti_feed(self, token: str, vs_id: str, feed_id: str, api_key: Optional[str] = None) -> Dict:
        payload: Dict[str, Optional[str]] = {"feed_id": feed_id}
        if api_key:
            payload["api_key"] = api_key
        resp = self._request(
            "POST",
            f"/api/virtual-services/{vs_id}/ti-feeds",
            json=payload,
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        return resp.json()

    def get_available_feeds(self, token: str) -> List[Dict]:
        resp = self._request(
            "GET",
            "/api/ti-feeds",
            headers=self._auth_headers(token)
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    def call_virtual_service(self, slug: str, path: str = "", token: Optional[str] = None,
                              params: Optional[Dict] = None) -> requests.Response:
        normalized_path = path if path.startswith("/") else f"/{path}" if path else ""
        url = f"{self.base_url}{self.path_prefix}/vs/{slug}{normalized_path}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
        return resp
