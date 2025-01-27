"""The Pstryk integration."""
from __future__ import annotations

import logging
import voluptuous as vol
import yaml
import os
import asyncio
from datetime import datetime, timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.util.async_ import run_callback_threadsafe
import async_timeout

from .const import DOMAIN
from .api import PstrykApiClient
from .ws import PstrykWebSocket

PLATFORMS: list[Platform] = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pstryk from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp.ClientSession()
    api_client = PstrykApiClient(
        entry.data["email"],
        entry.data["password"],
        session,
    )
    
    try:
        await api_client.authenticate()
    except Exception as err:
        await session.close()
        raise ConfigEntryNotReady from err

    ws_client = PstrykWebSocket(api_client, session)
    # Connect clients to each other
    api_client._ws_client = ws_client
    
    # Store both clients
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api_client,
        "ws": ws_client
    }

    async def handle_update_prices(call: ServiceCall) -> None:
        """Handle the service call."""
        coordinator = hass.data[DOMAIN]["coordinator"]
        await coordinator.async_refresh()

    async def handle_midnight_rollover():
        """Handle the midnight price rollover."""
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        
        # Get entity references
        tomorrow_sensor = None
        today_sensor = None
        
        for entity in hass.data[DOMAIN][entry.entry_id]["entities"]:
            if isinstance(entity, PstrykTomorrowsPricesSensor):
                tomorrow_sensor = entity
            elif isinstance(entity, PstrykTodaysPricesSensor):
                today_sensor = entity
        
        if tomorrow_sensor and today_sensor:
            # Get tomorrow's prices
            if (tomorrow_sensor.coordinator.data and 
                "tomorrow_prices" in tomorrow_sensor.coordinator.data):
                new_prices = dict(tomorrow_sensor.coordinator.data["tomorrow_prices"])
                # Update today's prices
                today_sensor.update_prices(new_prices)
            
            # Clear tomorrow's prices
            tomorrow_sensor.clear_prices()
            
            # Force coordinator update to get new tomorrow's prices
            await coordinator.async_refresh()

    async def midnight_timer():
        """Run timer for midnight updates."""
        while True:
            now = datetime.now()
            # Calculate time until next midnight
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            delay = (tomorrow - now).total_seconds()
            
            await asyncio.sleep(delay)
            await handle_midnight_rollover()

    # Register service
    hass.services.async_register(DOMAIN, "update_prices", handle_update_prices)

    # Create daily price update automation
    try:
        automation = {
            "id": f"{DOMAIN}_daily_price_update",
            "alias": "Update Pstryk Prices Daily",
            "description": "Automatically update electricity prices every day at 17:00",
            "trigger": [{
                "platform": "time",
                "at": "17:00:00"
            }],
            "action": [{
                "service": f"{DOMAIN}.update_prices"
            }],
            "mode": "single"
        }

        automation_file = os.path.join(hass.config.config_dir, "automations.yaml")
        
        existing_automations = []
        if os.path.exists(automation_file):
            # Run file operations in executor to avoid blocking
            def read_yaml():
                with open(automation_file, 'r') as f:
                    content = f.read()
                    if content:
                        return yaml.safe_load(content) or []
                return []

            existing_automations = await hass.async_add_executor_job(read_yaml)
            if not isinstance(existing_automations, list):
                existing_automations = []

        # Add automation if it doesn't exist
        if not any(a.get('id') == automation['id'] for a in existing_automations):
            existing_automations.append(automation)
            
            def write_yaml():
                with open(automation_file, 'w') as f:
                    yaml.dump(existing_automations, f)

            await hass.async_add_executor_job(write_yaml)
            await hass.services.async_call("automation", "reload")

    except Exception as err:
        _LOGGER.error("Failed to create automation: %s", err)

    # Start the midnight timer
    hass.loop.create_task(midnight_timer())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = hass.data[DOMAIN].pop(entry.entry_id)
        await client._session.close()
        
        # Remove service
        hass.services.async_remove(DOMAIN, "update_prices")

        # Remove automation
        automation_id = f"{DOMAIN}_daily_price_update"
        await hass.services.async_call(
            "automation",
            "remove",
            {"entity_id": f"automation.{automation_id}"}
        )
        
    return unload_ok
