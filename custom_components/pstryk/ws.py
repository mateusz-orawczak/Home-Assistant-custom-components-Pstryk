"""WebSocket client for Pstryk."""
from datetime import datetime, timedelta
import json
import logging
import asyncio
from typing import Dict, Optional, Callable

import aiohttp

from .const import WS_ENDPOINT

_LOGGER = logging.getLogger(__name__)

class PstrykWebSocket:
    """WebSocket client for Pstryk."""

    def __init__(self, api_client, session: aiohttp.ClientSession):
        """Initialize the WebSocket client."""
        self._api_client = api_client
        self._session = session
        self._ws = None
        self._ws_task = None
        self._ws_callback = None
        # Use the same data dictionary as API client
        self._last_data = api_client._last_data
        self._shutdown = False
        self._closing = False
        self._last_reconnect = datetime.now()
        self._reconnect_interval = timedelta(hours=2)
        self._first_message_ignored = True

    async def start_websocket(self, callback: Callable[[Dict], None]) -> None:
        """Start WebSocket connection."""
        if self._ws_task is not None:
            return

        self._ws_callback = callback
        self._shutdown = False
        self._ws_task = asyncio.create_task(self._websocket_loop())

    async def stop_websocket(self) -> None:
        """Stop WebSocket connection."""
        self._shutdown = True
        if self._ws:
            await self._ws.close()
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None

    async def _websocket_loop(self) -> None:
        """Maintain WebSocket connection."""
        retry_count = 0
        backoff = 5  # Start with 5 second delay
        max_backoff = 300  # Maximum 5 minutes delay
        
        while not self._shutdown:
            try:
                retry_count += 1
                _LOGGER.debug(
                    "WebSocket connection attempt %d",
                    retry_count,
                )
                
                await self._connect_websocket()
                # Reset backoff on successful connection
                retry_count = 0
                backoff = 5
                
            except aiohttp.ClientError as err:
                if self._shutdown:
                    break
                _LOGGER.error("WebSocket connection error: %s", err)
            except asyncio.CancelledError:
                break
            except Exception as err:
                if self._shutdown:
                    break
                _LOGGER.error("WebSocket unexpected error: %s", err)
            
            if not self._shutdown:
                # Exponential backoff with maximum limit
                await asyncio.sleep(min(backoff * 2 ** (retry_count - 1), max_backoff))

    async def _connect_websocket(self) -> None:
        """Connect to WebSocket and handle messages."""
        meter_id = self._api_client.meter_id
        if not meter_id:
            _LOGGER.error("WebSocket connection failed: No meter_id available")
            return

        ws_url = WS_ENDPOINT.format(meter_id=meter_id)
        _LOGGER.debug("Attempting WebSocket connection to: %s", ws_url)
        
        try:
            async with self._session.ws_connect(
                ws_url,
                headers={
                    "Sec-WebSocket-Protocol": self._api_client.access_token,
                },
                heartbeat=30,
            ) as websocket:
                self._ws = websocket
                self._last_reconnect = datetime.now()
                self._first_message_ignored = False  # Reset flag on new connection
                _LOGGER.debug("WebSocket connected successfully")

                async for msg in websocket:
                    # Check for periodic reconnection
                    if datetime.now() - self._last_reconnect >= self._reconnect_interval:
                        _LOGGER.debug("Performing scheduled WebSocket reconnection")
                        break  # This will trigger reconnection through the websocket loop
                        
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        try:
                            if not self._first_message_ignored:
                                self._first_message_ignored = True
                                _LOGGER.debug("Ignoring first message after connection")
                                continue
                                
                            data = json.loads(msg.data.decode())
                            _LOGGER.debug("PSTRYK - WebSocket message: %s", json.dumps(data, indent=2))
                            self._process_ws_message(data)
                        except json.JSONDecodeError:
                            _LOGGER.error("Invalid JSON in binary WebSocket message")
                        except UnicodeDecodeError:
                            _LOGGER.error("Failed to decode binary WebSocket message")
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        _LOGGER.debug("WebSocket connection closed")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("WebSocket connection error: %s", websocket.exception())
                        break
        except aiohttp.ClientResponseError as resp_err:
            if resp_err.status == 500:
                _LOGGER.debug("PSTRYK - WebSocket authentication error (500), attempting token refresh")
                if await self._api_client.refresh_token():
                    _LOGGER.debug("PSTRYK - Token refreshed successfully, retrying connection")
                    raise  # Re-raise to trigger reconnection with new token
                else:
                    _LOGGER.debug("PSTRYK - Token refresh failed")
            raise  # Re-raise other response errors
        except aiohttp.ClientError as client_err:
            _LOGGER.error("PSTRYK - WebSocket client error: %s", client_err)
            raise
        except Exception as err:
            _LOGGER.error("PSTRYK - WebSocket unexpected error: %s", err)
            raise
        finally:
            self._ws = None

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
            
            # Get current data from API client
            merged_data = dict(self._api_client._last_data)
            # Update with new usage data
            merged_data.update(usage_data)
            
            if self._ws_callback:
                self._ws_callback(merged_data)
        except Exception as err:
            _LOGGER.error("Error processing WebSocket message: %s", err) 