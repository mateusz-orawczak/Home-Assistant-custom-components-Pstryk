"""API client for Pstryk."""
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

import aiohttp
import async_timeout

from .const import (
    API_LOGIN_ENDPOINT,
    API_REFRESH_TOKEN_ENDPOINT,
    API_ME_ENDPOINT,
    API_TODAY_USAGE_ENDPOINT,
    API_WEEK_USAGE_ENDPOINT,
    API_MONTH_USAGE_ENDPOINT,
    API_TODAY_COST_ENDPOINT,
    API_WEEK_COST_ENDPOINT,
    API_MONTH_COST_ENDPOINT,
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

    async def authenticate(self) -> bool:
        """Authenticate with the API and get meter ID."""
        try:
            # First authenticate
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    API_LOGIN_ENDPOINT,
                    json={"email": self._email, "password": self._password},
                )
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data["access"]
                    self._refresh_token = data["refresh"]
                    self._token_expires = datetime.now() + timedelta(hours=1)
                    
                    # Now get the meter ID
                    return await self._fetch_meter_id()
                return False
        except Exception as err:
            _LOGGER.error("Error authenticating: %s", err)
            return False

    async def _fetch_meter_id(self) -> bool:
        """Fetch meter ID from /api/me endpoint."""
        # hardcoded for now
        self._meter_id = "3019"
        return True

        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    API_ME_ENDPOINT,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                if response.status == 200:
                    data = await response.json()
                    self._meter_id = data.get("meter_id")
                    if self._meter_id:
                        _LOGGER.info("Successfully retrieved meter ID: %s", self._meter_id)
                        return True
                    _LOGGER.error("No meter ID found in response")
                    return False
                return False
        except Exception as err:
            _LOGGER.error("Error fetching meter ID: %s", err)
            return False

    async def _make_api_call(self, endpoint_template: str) -> Optional[Dict]:
        """Make an API call with the meter ID."""
        if not self._meter_id:
            if not await self._fetch_meter_id():
                return None
        
        endpoint = endpoint_template.format(meter_id=self._meter_id)
        await self._ensure_token_valid()
        
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as err:
            _LOGGER.error("Error making API call to %s: %s", endpoint, err)
            return None

    async def _ensure_token_valid(self):
        """Ensure the access token is valid."""
        if not self._access_token or (self._token_expires and datetime.now() >= self._token_expires):
            if self._refresh_token and await self.refresh_token():
                return
            await self.authenticate()

    async def refresh_token(self) -> bool:
        """Refresh the access token."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    API_REFRESH_TOKEN_ENDPOINT,
                    headers={"Authorization": f"Bearer {self._refresh_token}"},
                )
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data["access"]
                    self._token_expires = datetime.now() + timedelta(hours=1)
                    return True
                return False
        except Exception as err:
            _LOGGER.error("Error refreshing token: %s", err)
            return False

    async def get_today_usage(self) -> dict | None:
        """Get today's energy usage data."""
        response = await self._make_api_call(API_TODAY_USAGE_ENDPOINT)
        if response:
            return {
                "usage": response.get("fae_total_usage"),
            }
        return None

    async def get_week_usage(self) -> dict | None:
        """Get this week's energy usage data."""
        response = await self._make_api_call(API_WEEK_USAGE_ENDPOINT)
        if response:
            return {
                "usage": response.get("fae_total_usage"),
            }
        return None

    async def get_month_usage(self) -> dict | None:
        """Get this month's energy usage data."""
        response = await self._make_api_call(API_MONTH_USAGE_ENDPOINT)
        if response:
            return {
                "usage": response.get("fae_total_usage"),
            }
        return None

    async def get_today_cost(self) -> dict | None:
        """Get today's energy cost data."""
        response = await self._make_api_call(API_TODAY_COST_ENDPOINT)
        if response:
            return {
                "cost": response.get("fae_total_cost"),
            }
        return None

    async def get_week_cost(self) -> dict | None:
        """Get this week's energy cost data."""
        response = await self._make_api_call(API_WEEK_COST_ENDPOINT)
        if response:
            return {
                "cost": response.get("fae_total_cost"),
            }
        return None

    async def get_month_cost(self) -> dict | None:
        """Get this month's energy cost data."""
        response = await self._make_api_call(API_MONTH_COST_ENDPOINT)
        if response:
            return {
                "cost": response.get("fae_total_cost"),
            }
        return None

    async def get_prices(self) -> dict | None:
        """Get energy prices."""
        response = await self._make_api_call(API_PRICES_ENDPOINT)
        if response:
            from datetime import datetime
            hourly_prices = {}
            current_price = None
            next_hour_price = None
            now = datetime.now()
            
            for frame in response.get("frames", []):
                start_time = frame.get("start")
                price = frame.get("price_gross")
                if start_time and price:
                    frame_time = datetime.fromisoformat(start_time)
                    hourly_prices[start_time] = price
                    # Find current price from frames
                    if frame_time.hour == now.hour:
                        current_price = price
                    # Find next hour price from frames
                    if frame_time.hour == (now.hour + 1) % 24:
                        next_hour_price = price

            return {
                "current_price": current_price,
                "next_hour_price": next_hour_price,
                "today_price_avg": response.get("price_gross_avg"),
                "hourly_prices": hourly_prices,
                "prices_updated": datetime.now().isoformat(),
            }
        return None

    async def get_all_data(self) -> dict | None:
        """Get all energy data."""
        today_usage = await self.get_today_usage()
        week_usage = await self.get_week_usage()
        month_usage = await self.get_month_usage()
        today_cost = await self.get_today_cost()
        week_cost = await self.get_week_cost()
        month_cost = await self.get_month_cost()
        prices = await self.get_prices()

        data = {
            "today_usage": today_usage.get("usage") if today_usage else None,
            "today_cost": today_cost.get("cost") if today_cost else None,
            "week_usage": week_usage.get("usage") if week_usage else None,
            "week_cost": week_cost.get("cost") if week_cost else None,
            "month_usage": month_usage.get("usage") if month_usage else None,
            "month_cost": month_cost.get("cost") if month_cost else None,
        }

        if prices:
            data.update(prices)

        return data
