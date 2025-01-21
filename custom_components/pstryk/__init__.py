"""The Pstryk integration."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .api import PstrykApiClient

PLATFORMS: list[Platform] = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pstryk from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp.ClientSession()
    client = PstrykApiClient(
        entry.data["email"],
        entry.data["password"],
        session,
    )

    try:
        await client.authenticate()
    except Exception as err:
        await session.close()
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = hass.data[DOMAIN].pop(entry.entry_id)
        await client._session.close()
    return unload_ok
