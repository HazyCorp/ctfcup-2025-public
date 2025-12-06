#!/usr/bin/env python3

import sys
import time
import traceback
from typing import Optional

import requests
from gornilo import NewChecker, Verdict, CheckRequest, PutRequest, GetRequest, VulnChecker

from api import TIServerAPI, WarehouseAPI, AuthServerAPI, GatewayAPI
from helpers import (
    generate_random_string,
    generate_random_ip,
    generate_random_domain,
    generate_feed_name,
    random_asset_type
)


class CommonChecker(NewChecker):

    def get_api(self, host: str) -> TIServerAPI:
        """Get API client instance"""
        return TIServerAPI(host, timeout=10, path_prefix="/ti")

    def get_warehouse_api(self, host: str) -> WarehouseAPI:
        """Get Warehouse API client"""
        return WarehouseAPI(host, timeout=10, warehouse_prefix="/warehouse", auth_prefix="/auth")

    def get_auth_api(self, host: str) -> AuthServerAPI:
        return AuthServerAPI(host, timeout=10, path_prefix="/auth")

    def get_gateway_api(self, host: str) -> GatewayAPI:
        return GatewayAPI(host, timeout=10, path_prefix="/gateway")

    def verify_ti_workflow(self, api: TIServerAPI) -> Optional[Verdict]:
        """Run TI server workflow check"""
        # 1. Check if we can get public feeds
        feeds = api.get_public_feeds()
        if not isinstance(feeds, list):
            return Verdict.MUMBLE("Expected list of feeds")

        # 2. Create a public test feed
        public_feed_name = generate_feed_name()
        public_feed_description = "Automated test public feed"

        public_feed_id, _ = api.create_feed(public_feed_name, public_feed_description, is_public=True)

        # 3. Verify we can get the created public feed
        feed = api.get_feed(public_feed_id)
        if feed["name"] != public_feed_name:
            return Verdict.MUMBLE("Public feed name mismatch")
        if feed["id"] != public_feed_id:
            return Verdict.MUMBLE("Public feed ID mismatch")

        # 4. Add a test IOC to public feed
        test_ip = generate_random_ip()
        ioc_description = f"Test IOC {generate_random_string(6)}"

        api.add_ioc(
            public_feed_id,
            "ip",
            test_ip,
            "high",
            ioc_description
        )

        # 5. Verify we can get IOCs from public feed
        iocs = api.get_iocs(public_feed_id)
        if not isinstance(iocs, list):
            return Verdict.MUMBLE("Expected list of IOCs")
        if len(iocs) != 1:
            return Verdict.MUMBLE(f"Expected 1 IOC, got {len(iocs)}")

        # 6. Verify IOC data
        ioc = iocs[0]
        if ioc["value"] != test_ip:
            return Verdict.MUMBLE("IOC value mismatch")
        if ioc["type"] != "ip":
            return Verdict.MUMBLE("IOC type mismatch")
        if ioc["description"] != ioc_description:
            return Verdict.MUMBLE("IOC description mismatch")

        # 7. Create a private test feed
        private_feed_name = generate_feed_name()
        private_feed_description = "Automated test private feed"

        private_feed_id, private_api_key = api.create_feed(private_feed_name, private_feed_description, is_public=False)

        if not private_api_key:
            return Verdict.MUMBLE("No API key returned for private feed")

        # 8. Verify we can get the created private feed with API key
        private_feed = api.get_feed(private_feed_id, private_api_key)
        if private_feed["name"] != private_feed_name:
            return Verdict.MUMBLE("Private feed name mismatch")
        if private_feed["id"] != private_feed_id:
            return Verdict.MUMBLE("Private feed ID mismatch")

        # 9. Add a test IOC to private feed
        private_test_domain = generate_random_domain()
        private_ioc_description = f"Private test IOC {generate_random_string(6)}"

        api.add_ioc(
            private_feed_id,
            "domain",
            private_test_domain,
            "critical",
            private_ioc_description,
            private_api_key
        )

        # 10. Verify we can get IOCs from private feed
        private_iocs = api.get_iocs(private_feed_id, private_api_key)
        if not isinstance(private_iocs, list):
            return Verdict.MUMBLE("Expected list of IOCs from private feed")
        if len(private_iocs) != 1:
            return Verdict.MUMBLE(f"Expected 1 IOC in private feed, got {len(private_iocs)}")

        # 11. Verify private IOC data
        private_ioc = private_iocs[0]
        if private_ioc["value"] != private_test_domain:
            return Verdict.MUMBLE("Private IOC value mismatch")
        if private_ioc["type"] != "domain":
            return Verdict.MUMBLE("Private IOC type mismatch")
        if private_ioc["description"] != private_ioc_description:
            return Verdict.MUMBLE("Private IOC description mismatch")

        # def scan_feeds(is_public: Optional[bool], expect_public_feed: bool, expect_private_feed: bool) -> Optional[Verdict]:
        #     """Scan feeds list and verify expected feeds are present/absent"""
        #     page_size = 10
        #     offset = 0
        #     found_public = False
        #     found_private = False
        #     max_pages = 100
        #     pages = 0
        #     all_feed_ids = []
        #     while True:
        #         page = api.get_feeds(is_public=is_public, limit=page_size, offset=offset)
        #         feeds_page = page.get("feeds", [])
        #         total = page.get("total", len(feeds_page))
        #         if not isinstance(feeds_page, list):
        #             return Verdict.MUMBLE("Invalid feeds response format")
        #         for feed in feeds_page:
        #             all_feed_ids.append(feed.get("id"))
        #             if "api_key" in feed and feed.get("api_key"):
        #                 return Verdict.MUMBLE("API key leaked in feeds list")
        #             if feed.get("id") == public_feed_id:
        #                 found_public = True
        #             if feed.get("id") == private_feed_id:
        #                 found_private = True
        #         offset += page_size
        #         pages += 1
        #         if offset >= total or len(feeds_page) == 0 or pages >= max_pages:
        #             break

        #     if expect_public_feed and not found_public:
        #         return Verdict.MUMBLE(f"Public feed {public_feed_id} not found in feeds list (is_public={is_public}). Found feeds: {all_feed_ids[:10]}")
        #     if not expect_public_feed and found_public:
        #         return Verdict.MUMBLE(f"Public feed unexpectedly found in feeds list (is_public={is_public})")

        #     if expect_private_feed and not found_private:
        #         return Verdict.MUMBLE(f"Private feed {private_feed_id} not found in feeds list (is_public={is_public}). Found feeds: {all_feed_ids[:10]}")
        #     if not expect_private_feed and found_private:
        #         return Verdict.MUMBLE(f"Private feed unexpectedly found in feeds list (is_public={is_public})")

        #     return None

        # 12. Check public feed appears in correct lists
        # Public feed should be in: public list and all list, but NOT in private list
        # verdict = scan_feeds(is_public=True, expect_public_feed=True, expect_private_feed=False)
        # if verdict:
        #     return verdict

        # verdict = scan_feeds(is_public=None, expect_public_feed=True, expect_private_feed=True)
        # if verdict:
        #     return verdict

        # verdict = scan_feeds(is_public=False, expect_public_feed=False, expect_private_feed=True)
        # if verdict:
        #     return verdict

        return None

    def verify_warehouse_workflow(self, host: str) -> Optional[Verdict]:
        """Run basic warehouse scenario"""
        warehouse_api = self.get_warehouse_api(host)

        username = f"user_{generate_random_string(8).lower()}"
        password = generate_random_string(16)
        email = f"{username}@example.com"

        user = warehouse_api.register_user(username, email, password)
        user_id = user.get("id") if isinstance(user, dict) else None
        token = warehouse_api.login(username, password)

        realm_name = f"Realm {generate_random_string(6)}"
        realm_description = "Automated realm for checker"
        realm = warehouse_api.create_realm(token, realm_name, realm_description)
        realm_id = realm.get("id")
        if not realm_id:
            return Verdict.MUMBLE("Realm ID missing in response")

        bartender_username = f"bartender_{generate_random_string(6).lower()}"
        bartender_password = generate_random_string(16)
        bartender_email = f"{bartender_username}@example.com"
        bartender_user = warehouse_api.register_user(bartender_username, bartender_email, bartender_password)
        bartender_id = bartender_user.get("id")
        if not bartender_id:
            return Verdict.MUMBLE("Bartender user ID missing")

        # Warehouse uses role "member" for bartenders
        warehouse_api.add_user_to_realm(token, realm_id, bartender_id, "member")

        realms = warehouse_api.get_realms(token)
        if not any(r.get("id") == realm_id for r in realms):
            return Verdict.MUMBLE("Created realm missing in list")

        asset_name = f"Asset {generate_random_string(6)}"
        asset_type = random_asset_type()
        asset_description = "Automated asset"
        asset = warehouse_api.create_asset(
            token,
            realm_id,
            asset_name,
            asset_type,
            asset_description,
            owner_user_id=bartender_id
        )
        asset_id = asset.get("id")
        if not asset_id:
            return Verdict.MUMBLE("Asset ID missing in response")

        assets_page = warehouse_api.get_realm_assets(token, realm_id)
        asset_list = assets_page.get("data") if isinstance(assets_page, dict) else assets_page
        if not isinstance(asset_list, list):
            return Verdict.MUMBLE("Invalid assets list format")
        if not any(a.get("id") == asset_id for a in asset_list):
            return Verdict.MUMBLE("Asset not found in realm listing")

        fetched_asset = warehouse_api.get_asset(token, asset_id)
        if fetched_asset.get("name") != asset_name:
            return Verdict.MUMBLE("Asset name mismatch")
        if fetched_asset.get("asset_type") != asset_type:
            return Verdict.MUMBLE("Asset type mismatch")
        if fetched_asset.get("realm_id") != realm_id:
            return Verdict.MUMBLE("Asset realm mismatch")

        # Verify bartender sees assigned asset
        bartender_token = warehouse_api.login(bartender_username, bartender_password)
        bartender_assets_page = warehouse_api.get_realm_assets(bartender_token, realm_id)
        bartender_assets = bartender_assets_page.get("data") if isinstance(bartender_assets_page, dict) else bartender_assets_page
        if not isinstance(bartender_assets, list):
            return Verdict.MUMBLE("Invalid bartender assets list format")
        if not any(a.get("id") == asset_id for a in bartender_assets):
            return Verdict.MUMBLE("Bartender cannot see assigned asset in realm listing")

        bartender_asset = warehouse_api.get_asset(bartender_token, asset_id)
        if bartender_asset.get("owner_user_id") != bartender_id:
            return Verdict.MUMBLE("Bartender asset owner mismatch")

        # Test user search functionality
        # Use more specific search query to reduce false negatives (longer substring)
        # Search with at least 10-12 characters to make it more specific
        min_query_len = min(12, len(username) - 1) if len(username) > 3 else 2
        search_query = username[:min_query_len]
        search_results = warehouse_api.search_users(token, search_query, limit=50)
        if not isinstance(search_results, list):
            return Verdict.MUMBLE("User search results should be a list")

        # Verify our user is in the search results
        found_user = False
        for search_user in search_results:
            if search_user.get("username") == username:
                found_user = True
                if user_id and search_user.get("id") != user_id:
                    return Verdict.MUMBLE("User search returned wrong user ID for main user")
                break

        if not found_user:
            return Verdict.MUMBLE(f"User search did not return created user (query: '{search_query}')")

        # Search for bartender by substring with more specific query
        min_bartender_query_len = min(12, len(bartender_username) - 1) if len(bartender_username) > 3 else 2
        bartender_search_query = bartender_username[:min_bartender_query_len]
        bartender_search_results = warehouse_api.search_users(token, bartender_search_query, limit=50)
        if not isinstance(bartender_search_results, list):
            return Verdict.MUMBLE("Bartender search results should be a list")

        found_bartender = False
        for search_user in bartender_search_results:
            if search_user.get("username") == bartender_username:
                found_bartender = True
                if search_user.get("id") != bartender_id:
                    return Verdict.MUMBLE("Bartender search returned wrong user ID")
                break

        if not found_bartender:
            return Verdict.MUMBLE(f"User search did not return bartender (query: '{bartender_search_query}')")

        return None

    def verify_gateway_workflow(self, host: str) -> Optional[Verdict]:
        """Verify gateway server: realm protection + TI integration"""
        gateway_api = self.get_gateway_api(host)
        warehouse_api = self.get_warehouse_api(host)
        ti_api = self.get_api(host)

        username = f"gateway_{generate_random_string(8).lower()}"
        password = generate_random_string(16)
        email = f"{username}@example.com"

        user = warehouse_api.register_user(username, email, password)
        user_id = user.get("id") if isinstance(user, dict) else None
        if not user_id:
            return Verdict.MUMBLE("Gateway user registration missing user ID")

        token = warehouse_api.login(username, password)

        gateway_login = gateway_api.login(username, password)
        gateway_token = gateway_login.get("token") if isinstance(gateway_login, dict) else None
        if not gateway_token:
            return Verdict.MUMBLE("Gateway login response missing token")
        gateway_user = gateway_login.get("user") or {}
        if gateway_user.get("id") != user_id:
            return Verdict.MUMBLE("Gateway login user mismatch")

        realm_name = f"Gateway Realm {generate_random_string(6)}"
        realm_description = "Gateway protected realm"
        realm = warehouse_api.create_realm(token, realm_name, realm_description)
        realm_id = realm.get("id")
        if not realm_id:
            return Verdict.MUMBLE("Gateway realm creation failed")

        asset_name = f"Protected Asset {generate_random_string(6)}"
        asset_description = "Asset behind gateway"
        asset = warehouse_api.create_asset(
            token,
            realm_id,
            asset_name,
            random_asset_type(),
            asset_description,
            owner_user_id=user_id
        )
        asset_id = asset.get("id")
        if not asset_id:
            return Verdict.MUMBLE("Gateway asset creation failed")

        slug = f"bar-{generate_random_string(6).lower()}"
        protection = warehouse_api.create_gateway_protection(
            token,
            realm_id,
            slug,
            require_auth=True,
            ti_mode="block",
            rate_limit_enabled=False,
            rate_limit_requests=5,
            rate_limit_window_sec=5,
            log_retention_minutes=5
        )

        vs_id = protection.get("vs_id")
        vs_slug = protection.get("vs_slug")
        if not vs_id or not vs_slug:
            return Verdict.MUMBLE("Gateway protection response missing IDs")
        if not protection.get("is_protected"):
            return Verdict.MUMBLE("Warehouse did not mark realm as protected")

        vs = gateway_api.get_virtual_service(gateway_token, vs_id)
        if vs.get("slug") != vs_slug:
            return Verdict.MUMBLE("Gateway returned mismatched slug")
        backend_url = vs.get("backend_url", "")
        if realm_id not in backend_url:
            return Verdict.MUMBLE("Gateway backend URL does not point to realm")
        if not vs.get("require_auth"):
            return Verdict.MUMBLE("Gateway virtual service missing auth enforcement")
        if vs.get("ti_mode") != "block":
            return Verdict.MUMBLE("Gateway TI mode mismatch")

        feed_name = generate_feed_name()
        feed_description = "Gateway private TI feed"
        feed_id, feed_key = ti_api.create_feed(feed_name, feed_description, is_public=False)
        if not feed_key:
            return Verdict.MUMBLE("Gateway TI feed missing API key")

        indicator_value = f"{generate_random_string(10).lower()}-ioc"
        ti_api.add_ioc(
            feed_id,
            "domain",
            indicator_value,
            "high",
            "Gateway IOC",
            feed_key
        )

        gateway_api.attach_ti_feed(gateway_token, vs_id, feed_id, feed_key)
        feeds = gateway_api.get_vs_feeds(gateway_token, vs_id)
        feed_entry = next((f for f in feeds if isinstance(f, dict) and f.get("feed_id") == feed_id), None)
        if not feed_entry:
            return Verdict.MUMBLE("Gateway did not report attached TI feed")
        if feed_entry.get("feed_name") != feed_name:
            return Verdict.MUMBLE("Gateway TI feed metadata mismatch")
        if not feed_entry.get("is_active"):
            return Verdict.MUMBLE("Gateway TI feed unexpectedly inactive")

        unauthorized_resp = gateway_api.call_virtual_service(vs_slug, "/assets")
        if unauthorized_resp.status_code != 401:
            return Verdict.MUMBLE(f"[verify_gateway_workflow] Gateway auth check failed: expected 401 Unauthorized, got {unauthorized_resp.status_code}")

        allowed_resp = gateway_api.call_virtual_service(vs_slug, "/assets", token=gateway_token)
        if allowed_resp.status_code == 429:
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway requests were rate limited unexpectedly")
        if allowed_resp.status_code != 200:
            return Verdict.MUMBLE(f"[verify_gateway_workflow] Gateway proxy failed: expected 200 OK, got {allowed_resp.status_code}")
        try:
            assets_payload = allowed_resp.json()
        except ValueError:
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway proxy response is not valid JSON")

        assets_list = assets_payload.get("data") if isinstance(assets_payload, dict) else None
        if not isinstance(assets_list, list):
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway assets payload format invalid")
        if not any(isinstance(a, dict) and a.get("id") == asset_id for a in assets_list):
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway proxy did not return created asset")

        block_deadline = time.time() + 10
        ti_blocked = False
        rate_limited_during_ti = False
        while time.time() < block_deadline:
            ti_block_resp = gateway_api.call_virtual_service(
                vs_slug,
                "/assets",
                token=gateway_token,
                params={"search": indicator_value}
            )
            if ti_block_resp.status_code == 403:
                ti_blocked = True
                break
            if ti_block_resp.status_code == 429:
                rate_limited_during_ti = True
            time.sleep(1)

        if not ti_blocked and rate_limited_during_ti:
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway requests were rate limited unexpectedly during TI check")
        if not ti_blocked:
            return Verdict.MUMBLE("[verify_gateway_workflow] Gateway did not block IOC request with TI protection")

        return None

    def verify_auth_server(self, host: str) -> Optional[Verdict]:
        """Run auth-server registration/login workflow"""
        auth_api = self.get_auth_api(host)
        username = f"auth_{generate_random_string(8).lower()}"
        email = f"{username}@example.com"
        password = generate_random_string(16)

        auth_api.register_user(username, email, password)

        login_resp = auth_api.login(username, password)
        token = login_resp.get("token")
        if not token:
            return Verdict.MUMBLE("Auth login response missing token")

        profile = auth_api.get_profile(token)
        if profile.get("username") != username:
            return Verdict.MUMBLE("Auth profile username mismatch")
        if profile.get("email") != email:
            return Verdict.MUMBLE("Auth profile email mismatch")
        user_id = profile.get("id")
        if not user_id:
            return Verdict.MUMBLE("Auth profile missing user ID")

        # page_size = 10
        # offset = 0
        # found = False
        # max_iterations = 50
        # iterations = 0
        # while True:
        #     users_page = auth_api.list_users(token, limit=page_size, offset=offset)
        #     users = users_page.get("users")
        #     if not isinstance(users, list):
        #         return Verdict.MUMBLE("Auth users response missing users list")
        #     total = users_page.get("total")
        #     if not isinstance(total, int):
        #         return Verdict.MUMBLE("Auth users response missing total")
        #     for user in users:
        #         if isinstance(user, dict) and user.get("id") == user_id:
        #             found = True
        #             break
        #     if found:
        #         break
        #     offset += page_size
        #     iterations += 1
        #     if offset >= total or iterations >= max_iterations:
        #         break

        # if not found:
        #     return Verdict.MUMBLE("New user not found in paginated users list")

        logout_resp = auth_api.logout(token)
        if logout_resp.get("message") != "Logged out successfully":
            return Verdict.MUMBLE("Auth logout failed")

        public_key = auth_api.get_public_key()
        if not public_key.get("public_key"):
            return Verdict.MUMBLE("Auth public key missing")

        return None


checker = CommonChecker()

# Register check handler
@checker.define_check
def check(request: CheckRequest) -> Verdict:
    """Check TI server and Warehouse workflows"""
    api = checker.get_api(request.hostname)

    try:
        ti_verdict = checker.verify_ti_workflow(api)
        if ti_verdict:
            return ti_verdict

        warehouse_verdict = checker.verify_warehouse_workflow(request.hostname)
        if warehouse_verdict:
            return warehouse_verdict

        gateway_verdict = checker.verify_gateway_workflow(request.hostname)
        if gateway_verdict:
            return gateway_verdict

        auth_verdict = checker.verify_auth_server(request.hostname)
        if auth_verdict:
            return auth_verdict

        return Verdict.OK()

    except requests.exceptions.ConnectionError as e:
        return Verdict.DOWN("Service is down")
    except requests.exceptions.Timeout as e:
        return Verdict.DOWN("Service timeout")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code >= 500:
            return Verdict.DOWN("Service returned 5xx")
        return Verdict.MUMBLE(f"Unexpected HTTP status: {e.response.status_code}")
    except Exception as e:
        traceback.print_exc()
        return Verdict.MUMBLE(f"Checker error: {str(e)}")
    
@checker.define_vuln("")
class FeedVuln(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        """Put flag for vuln 1: Flag in IOC value (domain)"""
        api = checker.get_api(request.hostname)
        flag = request.flag

        try:
            feed_name = generate_feed_name()
            feed_description = f"Private intelligence collection {generate_random_string(8)}"
            feed_id, api_key = api.create_feed(feed_name, feed_description, is_public=False)

            if not api_key:
                return Verdict.MUMBLE("No API key returned for private feed")

            # Vuln 1: Flag in IOC value (domain)
            domain_value = f"{flag}.malicious.local"
            ioc_id = api.add_ioc(feed_id, "domain", domain_value, "critical", "Command and control server detected", api_key)

            # Verify flag can be retrieved
            feed = api.get_feed(feed_id, api_key)
            if feed["id"] != feed_id:
                return Verdict.MUMBLE("Feed verification failed")

            iocs = api.get_iocs(feed_id, api_key)
            if len(iocs) == 0:
                return Verdict.MUMBLE("No IOCs found after creation")

            flag_id = f"{feed_id}:{api_key}"
            return Verdict.OK_WITH_FLAG_ID(feed_id, flag_id)

        except requests.exceptions.ConnectionError as e:
            return Verdict.DOWN("Service is down")
        except requests.exceptions.Timeout as e:
            return Verdict.DOWN("Service timeout")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                return Verdict.DOWN("Service returned 5xx")
            return Verdict.MUMBLE(f"Unexpected HTTP status: {e.response.status_code}")
        except Exception as e:
            traceback.print_exc()
            return Verdict.MUMBLE(f"Checker error: {str(e)}")

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        """Get flag for vuln 1: Flag in IOC value (domain)"""
        api = checker.get_api(request.hostname)
        flag = request.flag
        flag_id = request.flag_id

        try:
            # Parse flag_id and strip whitespace
            parts = flag_id.strip().split(":")
            if len(parts) != 2:
                return Verdict.MUMBLE("Invalid flag_id format")
            feed_id, api_key = parts[0].strip(), parts[1].strip()

            # Get feed
            try:
                feed = api.get_feed(feed_id, api_key)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    return Verdict.CORRUPT("Unauthorized access - flag corrupted")
                if e.response.status_code == 404:
                    return Verdict.CORRUPT("Feed not found - flag corrupted")
                raise

            if feed["id"] != feed_id:
                return Verdict.CORRUPT("Feed ID mismatch")

            # Get IOCs
            iocs = api.get_iocs(feed_id, api_key)
            if not isinstance(iocs, list):
                return Verdict.MUMBLE("Expected list of IOCs")
            if len(iocs) == 0:
                return Verdict.CORRUPT("No IOCs found - flag corrupted")

            # Find flag in domain IOC value
            flag_found = False
            for ioc in iocs:
                if ioc["type"] == "domain" and flag in ioc["value"]:
                    flag_found = True
                    break

            if not flag_found:
                return Verdict.CORRUPT("Flag not found in IOCs")

            return Verdict.OK()

        except requests.exceptions.ConnectionError as e:
            return Verdict.DOWN("Service is down")
        except requests.exceptions.Timeout as e:
            return Verdict.DOWN("Service timeout")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                return Verdict.DOWN("Service returned 5xx")
            if e.response.status_code == 404 or e.response.status_code == 401:
                return Verdict.CORRUPT("Flag corrupted or removed")
            return Verdict.MUMBLE(f"Unexpected HTTP status: {e.response.status_code}")
        except Exception as e:
            traceback.print_exc()
            return Verdict.MUMBLE(f"Checker error: {str(e)}")


    

@checker.define_vuln("")
class GWVuln(VulnChecker):
    @staticmethod
    def put(request: PutRequest) -> Verdict:
        """Put flag for vuln 2: Flag in user email"""
        auth_api = checker.get_auth_api(request.hostname)
        flag = request.flag

        try:
            # Vuln 2: Flag in email field
            username = f"user_{generate_random_string(8).lower()}"
            password = generate_random_string(16)
            # Embed flag directly in email
            email = f"{flag}@example.com"

            user = auth_api.register_user(username, email, password)
            user_id = user.get("id")
            if not user_id:
                return Verdict.MUMBLE("User ID missing in registration response")

            # Verify flag can be retrieved via login
            login_resp = auth_api.login(username, password)
            token = login_resp.get("token")
            if not token:
                return Verdict.MUMBLE("Token missing in login response")

            # Verify profile contains the email with flag
            profile = auth_api.get_profile(token)
            if profile.get("email") != email:
                return Verdict.MUMBLE("Profile email mismatch")

            # Return credentials for retrieval
            flag_id = f"{username}:{password}"
            return Verdict.OK_WITH_FLAG_ID(username, flag_id)

        except requests.exceptions.ConnectionError as e:
            return Verdict.DOWN("Service is down")
        except requests.exceptions.Timeout as e:
            return Verdict.DOWN("Service timeout")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                return Verdict.DOWN("Service returned 5xx")
            return Verdict.MUMBLE(f"Unexpected HTTP status: {e.response.status_code}")
        except Exception as e:
            traceback.print_exc()
            return Verdict.MUMBLE(f"Checker error: {str(e)}")

    @staticmethod
    def get(request: GetRequest) -> Verdict:
        """Get flag for vuln 2: Flag in user email"""
        auth_api = checker.get_auth_api(request.hostname)
        flag = request.flag
        flag_id = request.flag_id

        try:
            # Parse flag_id and strip whitespace
            parts = flag_id.strip().split(":")
            if len(parts) != 2:
                return Verdict.MUMBLE("Invalid flag_id format")
            username, password = parts[0].strip(), parts[1].strip()

            # Login
            try:
                login_resp = auth_api.login(username, password)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    return Verdict.CORRUPT("Unauthorized - user credentials corrupted")
                if e.response.status_code == 404:
                    return Verdict.CORRUPT("User not found - flag corrupted")
                raise

            token = login_resp.get("token")
            if not token:
                return Verdict.MUMBLE("Token missing in login response")

            # Get profile
            try:
                profile = auth_api.get_profile(token)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    return Verdict.CORRUPT("Unauthorized - token invalid")
                if e.response.status_code == 404:
                    return Verdict.CORRUPT("Profile not found - flag corrupted")
                raise

            email = profile.get("email", "")
            if not email:
                return Verdict.CORRUPT("Email missing from profile")

            # Check if flag is in email
            if flag not in email:
                return Verdict.CORRUPT("Flag not found in email")

            return Verdict.OK()

        except requests.exceptions.ConnectionError as e:
            return Verdict.DOWN("Service is down")
        except requests.exceptions.Timeout as e:
            return Verdict.DOWN("Service timeout")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                return Verdict.DOWN("Service returned 5xx")
            if e.response.status_code == 404 or e.response.status_code == 401:
                return Verdict.CORRUPT("Flag corrupted or removed")
            return Verdict.MUMBLE(f"Unexpected HTTP status: {e.response.status_code}")
        except Exception as e:
            traceback.print_exc()
            return Verdict.MUMBLE(f"Checker error: {str(e)}")
    


if __name__ == "__main__":
    checker.run()
