"""Dreame Vacuum Cloud API client."""
from __future__ import annotations

import hashlib
import json
import logging
import time
import base64
from typing import Any

import aiohttp

from .const import (
    AUTH_URL_TEMPLATE,
    API_URL_TEMPLATE,
    DEVICE_LIST_URL_TEMPLATE,
    BASIC_AUTH,
    USER_AGENT,
    TENANT_ID,
    PASSWORD_SALT,
)

_LOGGER = logging.getLogger(__name__)


class DreameCloudAuth:
    """Handles Dreame cloud authentication and token management."""

    def __init__(
        self,
        username: str,
        password: str,
        region: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.username = username
        self._password = password
        self.region = region
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._token_expiry: float = 0

        if access_token:
            self._parse_token_expiry(access_token)

    def _parse_token_expiry(self, token: str) -> None:
        """Parse JWT expiry from access token."""
        try:
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            decoded = json.loads(base64.b64decode(payload))
            self._token_expiry = decoded.get("exp", 0) - 60  # 60s buffer
        except Exception:
            self._token_expiry = 0

    @property
    def _auth_url(self) -> str:
        return AUTH_URL_TEMPLATE.format(region=self.region)

    @property
    def _headers(self) -> dict:
        return {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "en-US;q=0.8",
            "User-Agent": USER_AGENT,
            "Authorization": BASIC_AUTH,
            "Tenant-Id": TENANT_ID,
        }

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with Dreame salt."""
        return hashlib.md5((password + PASSWORD_SALT).encode("utf-8")).hexdigest()

    async def login(self, session: aiohttp.ClientSession) -> bool:
        """Perform password login to get tokens."""
        pwd_hash = self.hash_password(self._password)
        data = (
            f"platform=IOS&scope=all&grant_type=password"
            f"&username={self.username}&password={pwd_hash}&type=account"
        )
        try:
            async with session.post(
                self._auth_url, headers=self._headers, data=data, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error("Login failed: HTTP %s", resp.status)
                    return False
                result = await resp.json(content_type=None)
                if "access_token" not in result:
                    _LOGGER.error("Login failed: %s", result)
                    return False
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token")
                self._parse_token_expiry(self.access_token)
                _LOGGER.debug("Login successful")
                return True
        except Exception as exc:
            _LOGGER.error("Login error: %s", exc)
            return False

    async def refresh(self, session: aiohttp.ClientSession) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            _LOGGER.warning("No refresh token, falling back to password login")
            return await self.login(session)
        data = f"platform=IOS&scope=all&grant_type=refresh_token&refresh_token={self.refresh_token}"
        try:
            async with session.post(
                self._auth_url, headers=self._headers, data=data, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Token refresh failed (HTTP %s), retrying login", resp.status)
                    return await self.login(session)
                result = await resp.json(content_type=None)
                if "access_token" not in result:
                    _LOGGER.warning("Token refresh returned no token, retrying login")
                    return await self.login(session)
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                self._parse_token_expiry(self.access_token)
                _LOGGER.debug("Token refreshed successfully")
                return True
        except Exception as exc:
            _LOGGER.error("Token refresh error: %s", exc)
            return False

    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        return time.time() >= self._token_expiry

    async def ensure_valid_token(self, session: aiohttp.ClientSession) -> bool:
        """Ensure we have a valid access token, refreshing if needed."""
        if not self.access_token or self.is_token_expired():
            return await self.refresh(session)
        return True


class DreameCloudClient:
    """Client for Dreame cloud API."""

    def __init__(self, auth: DreameCloudAuth, device_id: str, host_prefix: str) -> None:
        self.auth = auth
        self.device_id = device_id
        self.host_prefix = host_prefix
        self._request_id = 1

    @property
    def _api_url(self) -> str:
        return API_URL_TEMPLATE.format(region=self.auth.region, host_prefix=self.host_prefix)

    @property
    def _api_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.auth.access_token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Dreame-Auth": self.auth.access_token,
            "Tenant-Id": TENANT_ID,
        }

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def get_properties(
        self, session: aiohttp.ClientSession, props: list[tuple[int, int]]
    ) -> dict[tuple[int, int], Any]:
        """Get multiple properties. Returns {(siid, piid): value}."""
        if not await self.auth.ensure_valid_token(session):
            raise AuthenticationError("Failed to authenticate")

        req_id = self._next_id()
        params = [{"did": self.device_id, "siid": s, "piid": p} for s, p in props]
        payload = {
            "did": self.device_id,
            "id": req_id,
            "data": {
                "did": self.device_id,
                "id": req_id,
                "method": "get_properties",
                "params": params,
            },
        }
        async with session.post(
            self._api_url,
            headers=self._api_headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)

        if not result.get("success"):
            raise APIError(f"API error: {result}")

        output = {}
        for item in result.get("data", {}).get("result", []):
            if item.get("code", -1) == 0:
                output[(item["siid"], item["piid"])] = item["value"]
        return output

    async def call_action(
        self,
        session: aiohttp.ClientSession,
        siid: int,
        aiid: int,
        params: list[dict] | None = None,
    ) -> bool:
        """Call a device action."""
        if not await self.auth.ensure_valid_token(session):
            raise AuthenticationError("Failed to authenticate")

        req_id = self._next_id()
        in_params = params or []
        payload = {
            "did": self.device_id,
            "id": req_id,
            "data": {
                "did": self.device_id,
                "id": req_id,
                "method": "action",
                "params": {"siid": siid, "aiid": aiid, "in": in_params},
            },
        }
        async with session.post(
            self._api_url,
            headers=self._api_headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)

        if not result.get("success"):
            raise APIError(f"Action failed: {result}")
        return result.get("data", {}).get("result", {}).get("code", -1) == 0

    async def get_devices(self, session: aiohttp.ClientSession) -> list[dict]:
        """List all devices on the account."""
        if not await self.auth.ensure_valid_token(session):
            raise AuthenticationError("Failed to authenticate")

        url = DEVICE_LIST_URL_TEMPLATE.format(region=self.auth.region)
        headers = {
            "Authorization": f"Bearer {self.auth.access_token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Dreame-Auth": self.auth.access_token,
            "Tenant-Id": TENANT_ID,
        }
        async with session.post(url, headers=headers, json={}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)

        if not result.get("success"):
            raise APIError(f"Device list error: {result}")
        return result.get("data", {}).get("page", {}).get("records", [])


class AuthenticationError(Exception):
    """Authentication failed."""


class APIError(Exception):
    """API returned an error."""
