"""API client for Pstryk."""
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Optional, Callable
import asyncio

import aiohttp
import async_timeout

from .const import (
    API_LOGIN_ENDPOINT,
    API_REFRESH_TOKEN_ENDPOINT,
    API_METER_ENDPOINT,
    API_PRICES_ENDPOINT,
    WS_ENDPOINT,
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
        self._ws = None
        self._ws_task = None
        self._ws_callback = None
        self._last_data = {}

    async def authenticate(self) -> bool:
        """Authenticate with the API and get meter ID."""
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
                    self._token_expires = datetime.now() + timedelta(minutes=10)
                    
                    return await self._fetch_meter_id()
                return False
        except Exception as err:
            _LOGGER.error("Error authenticating: %s", err)
            return False

    async def start_websocket(self, callback: Callable[[Dict], None]) -> None:
        """Start WebSocket connection."""
        if self._ws_task is not None:
            return

        self._ws_callback = callback
        self._ws_task = asyncio.create_task(self._websocket_loop())

    async def _websocket_loop(self) -> None:
        """Maintain WebSocket connection."""
        retry_count = 0
        
        while True:
            try:
                retry_count += 1
                _LOGGER.error(
                    "PSTRYK - WebSocket connection attempt %d",
                    retry_count,
                )
                
                await self._connect_websocket()
            except Exception as err:
                _LOGGER.error("WebSocket error: %s", err)
                await asyncio.sleep(5)  # Wait before reconnecting

    async def _connect_websocket(self) -> None:
        """Connect to WebSocket and handle messages."""
        if not self._meter_id:
            _LOGGER.error("PSTRYK - WebSocket connection failed: No meter_id available")
            if not await self._fetch_meter_id():
                return

        ws_url = WS_ENDPOINT.format(meter_id=self._meter_id)
        _LOGGER.error("PSTRYK - Attempting WebSocket connection to: %s", ws_url)
        
        try:
            async with self._session.ws_connect(
                ws_url,
                headers={
                    "Sec-WebSocket-Protocol": self._access_token,
                },
            ) as websocket:
                self._ws = websocket
                _LOGGER.error("PSTRYK - WebSocket connected successfully")

                async for msg in websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            _LOGGER.error("PSTRYK - WebSocket received text message: %s", msg.data[:200])
                            self._process_ws_message(data)
                        except json.JSONDecodeError:
                            _LOGGER.error("PSTRYK - Invalid JSON in WebSocket message: %s", msg.data[:200])
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        try:
                            data = json.loads(msg.data.decode())
                            _LOGGER.error("PSTRYK - WebSocket received binary message: %s", str(data)[:200])
                            self._process_ws_message(data)
                        except json.JSONDecodeError:
                            _LOGGER.error("PSTRYK - Invalid JSON in binary WebSocket message")
                        except UnicodeDecodeError:
                            _LOGGER.error("PSTRYK - Failed to decode binary WebSocket message")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("PSTRYK - WebSocket connection error: %s", websocket.exception())
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        _LOGGER.error("PSTRYK - WebSocket connection closed")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        _LOGGER.error("PSTRYK - WebSocket closing")
                        break
                    else:
                        _LOGGER.error("PSTRYK - Unexpected WebSocket message type: %s", msg.type)
        except aiohttp.ClientResponseError as resp_err:
            if resp_err.status == 500:
                _LOGGER.error("PSTRYK - WebSocket authentication error (500), attempting token refresh")
                if await self.refresh_token():
                    _LOGGER.error("PSTRYK - Token refreshed successfully, retrying connection")
                    raise  # Re-raise to trigger reconnection with new token
                else:
                    _LOGGER.error("PSTRYK - Token refresh failed")
            raise  # Re-raise other response errors
        except aiohttp.ClientError as client_err:
            _LOGGER.error("PSTRYK - WebSocket client error: %s", client_err)
            raise
        except Exception as err:
            _LOGGER.error("PSTRYK - WebSocket unexpected error: %s", err)
            raise

    def _process_ws_message(self, data: Dict) -> None:
        """Process WebSocket message and update data."""
        try:
            usage_data = {
                "today_usage": data.get("day_to_date", {}).get("fae_usage"),
                "today_cost": data.get("day_to_date", {}).get("fae_cost"),
                "week_usage": data.get("week_to_date", {}).get("fae_usage"),
                "week_cost": data.get("week_to_date", {}).get("fae_cost"),
                "month_usage": data.get("month_to_date", {}).get("fae_usage"),
                "month_cost": data.get("month_to_date", {}).get("fae_cost"),
            }
            
            self._last_data.update(usage_data)
            
            if self._ws_callback:
                self._ws_callback(self._last_data)
        except Exception as err:
            _LOGGER.error("Error processing WebSocket message: %s", err)

    async def _fetch_meter_id(self) -> bool:
        """Fetch meter ID from /api/me endpoint."""
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
                _LOGGER.error("PSTRYK - API call status %s from %s", response.status, endpoint)
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
                    json={"refresh": self._access_token}
                )
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data["access"]
                    self._token_expires = datetime.now() + timedelta(minutes=10)
                    return True
                return False
        except Exception as err:
            _LOGGER.error("Error refreshing token: %s", err)
            return False

    async def get_prices(self) -> Optional[Dict]:
        """Get energy prices."""
        response = await self._make_api_call(API_PRICES_ENDPOINT)
        if response:
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

            price_data = {
                "current_price": current_price,
                "next_hour_price": next_hour_price,
                "today_price_avg": response.get("price_gross_avg"),
                "hourly_prices": hourly_prices,
                "prices_updated": datetime.now().isoformat(),
            }
            
            self._last_data.update(price_data)
            return self._last_data
        return None
