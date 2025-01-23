"""API client for Pstryk."""
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
import json

import aiohttp
import async_timeout

from .const import (
    API_LOGIN_ENDPOINT,
    API_REFRESH_TOKEN_ENDPOINT,
    API_METER_ENDPOINT,
    API_PRICES_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

class PstrykApiClient:
    """API client for Pstryk."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._session = session
        self._access_token = None
        self._refresh_token = None
        self._token_expires = None
        self._meter_id = None
        self._last_data = {}
        self._coordinator = None  # Will be set by sensor.py
        self._ws_client = None  # Will be set later

    async def authenticate(self) -> bool:
        """Authenticate with the API and get meter ID."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.error("PSTRYK - Authenticating with email: %s", self._email)
                response = await self._session.post(
                    API_LOGIN_ENDPOINT,
                    json={"email": self._email, "password": self._password},
                )
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.error("PSTRYK - Authentication successful")
                    self._access_token = data["access"]
                    self._refresh_token = data["refresh"]
                    self._token_expires = datetime.now() + timedelta(minutes=10)
                    
                    return await self._fetch_meter_id()
                _LOGGER.error("PSTRYK - Authentication failed with status: %s", response.status)
                return False
        except Exception as err:
            _LOGGER.error("Error authenticating: %s", err)
            return False

    async def refresh_token(self) -> bool:
        """Refresh the access token."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.error("PSTRYK - Refreshing token using refresh token: %s", self._refresh_token)
                response = await self._session.post(
                    API_REFRESH_TOKEN_ENDPOINT,
                    json={"refresh": self._refresh_token},
                )
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.error("PSTRYK - Token refresh response: %s", json.dumps(data, indent=2))
                    self._access_token = data["access"]
                    self._token_expires = datetime.now() + timedelta(minutes=10)
                    return True
                _LOGGER.error("PSTRYK - Token refresh failed with status: %s", response.status)
                return False
        except Exception as err:
            _LOGGER.error("PSTRYK - Error refreshing token: %s", err)
            return False

    async def _fetch_meter_id(self) -> bool:
        """Fetch meter ID from API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    API_METER_ENDPOINT,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list) and len(data) > 0:
                        self._meter_id = data[0].get("id")
                        if self._meter_id:
                            _LOGGER.info("Successfully retrieved meter ID: %s", self._meter_id)
                            return True
                    _LOGGER.error("No meter ID found in response")
                    return False
                return False
        except Exception as err:
            _LOGGER.error("Error fetching meter ID: %s", err)
            return False

    async def get_prices(self) -> Optional[Dict]:
        """Get energy prices."""
        response = await self._make_api_call(API_PRICES_ENDPOINT)
        if response:
            hourly_prices = {}
            now = datetime.now()
            
            for frame in response.get("frames", []):
                start_time = frame.get("start")
                price = frame.get("price_gross")
                if start_time and price:
                    hourly_prices[start_time] = price

            price_data = {
                "hourly_prices": hourly_prices,
                "today_price_avg": response.get("today_price_avg"),
                "prices_updated": datetime.now().isoformat(),
            }
            
            # Get current data from coordinator
            if self._coordinator and self._coordinator.data:
                merged_data = dict(self._coordinator.data)
            else:
                merged_data = {}
            
            # Update with new price data
            merged_data.update(price_data)
            self._last_data = merged_data
            
            return self._last_data
        return None

    async def _make_api_call(self, endpoint: str) -> Optional[Dict]:
        """Make an API call."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.error("PSTRYK - Making API call to: %s", endpoint)
                response = await self._session.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.error("PSTRYK - API response: %s", json.dumps(data, indent=2))
                    return data
                _LOGGER.error("PSTRYK - API call failed with status: %s", response.status)
                return None
        except Exception as err:
            _LOGGER.error("API call error: %s", err)
            return None

    @property
    def meter_id(self) -> Optional[str]:
        """Get meter ID."""
        return self._meter_id

    @property
    def access_token(self) -> Optional[str]:
        """Get access token."""
        return self._access_token
