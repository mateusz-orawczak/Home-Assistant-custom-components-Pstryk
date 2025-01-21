"""API client for Pstryk."""
from datetime import datetime, timedelta
import logging
import aiohttp
import async_timeout

from .const import (
    API_LOGIN_ENDPOINT,
    API_REFRESH_TOKEN_ENDPOINT,
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

    async def authenticate(self) -> bool:
        """Authenticate with the API."""
        try:
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
                    return True
                return False
        except Exception as err:
            _LOGGER.error("Error authenticating: %s", err)
            return False

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

    async def _ensure_token_valid(self):
        """Ensure the access token is valid."""
        if not self._access_token or (self._token_expires and datetime.now() >= self._token_expires):
            if self._refresh_token and await self.refresh_token():
                return
            await self.authenticate()

    async def _make_api_call(self, endpoint: str) -> dict | None:
        """Make an API call with token handling."""
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
                "cost": response.get("fae_cost"),
            }
        return None

    async def get_week_cost(self) -> dict | None:
        """Get this week's energy cost data."""
        response = await self._make_api_call(API_WEEK_COST_ENDPOINT)
        if response:
            return {
                "cost": response.get("fae_cost"),
            }
        return None

    async def get_month_cost(self) -> dict | None:
        """Get this month's energy cost data."""
        response = await self._make_api_call(API_MONTH_COST_ENDPOINT)
        if response:
            return {
                "cost": response.get("fae_cost"),
            }
        return None

    async def get_all_data(self) -> dict | None:
        """Get all energy usage and cost data."""
        today_usage = await self.get_today_usage()
        week_usage = await self.get_week_usage()
        month_usage = await self.get_month_usage()
        today_cost = await self.get_today_cost()
        week_cost = await self.get_week_cost()
        month_cost = await self.get_month_cost()

        if not all([today_usage, week_usage, month_usage, today_cost, week_cost, month_cost]):
            return None

        return {
            "today_usage": today_usage.get("usage"),
            "today_cost": today_cost.get("cost"),
            "week_usage": week_usage.get("usage"),
            "week_cost": week_cost.get("cost"),
            "month_usage": month_usage.get("usage"),
            "month_cost": month_cost.get("cost"),
        }

    async def get_prices(self) -> dict | None:
        """Get energy prices."""
        return await self._make_api_call(API_PRICES_ENDPOINT)
