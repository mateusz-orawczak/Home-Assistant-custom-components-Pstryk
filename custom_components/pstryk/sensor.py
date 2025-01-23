"""Platform for sensor integration."""
from __future__ import annotations
from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.template import Template

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

class PstrykTemplateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk template sensor."""

    def __init__(self, hass, coordinator, name, unique_id, template_str):
        """Initialize the template sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{unique_id}"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._template = Template(template_str, hass)
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            return self._template.async_render()
        except Exception as err:
            _LOGGER.error("Error rendering template: %s", err)
            return None

class PstrykIsCheapestSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk is cheapest sensor."""

    def __init__(self, coordinator):
        """Initialize the is cheapest sensor."""
        super().__init__(coordinator)
        self._attr_name = "Is Cheapest Electricity Price"
        self._attr_unique_id = f"{DOMAIN}_is_cheapest_price"
        self._attr_icon = "mdi:cash-check"
        self._attr_device_class = None  # Binary sensors don't use device class
        self._attr_state_class = None   # Binary sensors don't use state class
        self._attr_native_unit_of_measurement = None  # Boolean sensors don't have units

    @property
    def native_value(self) -> str | None:
        """Return if current price is the cheapest."""
        if self.coordinator.data is None or "hourly_prices" not in self.coordinator.data:
            return None
            
        prices = self.coordinator.data.get("hourly_prices", {})
        if not prices:
            return None

        current_hour = datetime.now().strftime('%Y-%m-%dT%H:00:00+00:00')
        current_price = prices.get(current_hour)
        
        if current_price is None:
            return None
            
        min_price = min(prices.values())
        # Return string 'on'/'off' instead of boolean for better HA compatibility
        return "on" if current_price == min_price else "off"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pstryk sensors."""
    api_client = hass.data[DOMAIN][entry.entry_id]["api"]
    ws_client = hass.data[DOMAIN][entry.entry_id]["ws"]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="pstryk",
        update_method=api_client.get_prices,
    )

    # Store coordinator reference in API client
    api_client._coordinator = coordinator

    # Store coordinator in hass.data for service access
    hass.data[DOMAIN]["coordinator"] = coordinator

    # Start WebSocket connection
    await ws_client.start_websocket(coordinator.async_set_updated_data)
    
    # Initial price fetch
    await coordinator.async_refresh()

    entities = []
    
    # Add regular sensors
    for sensor_type, sensor_info in SENSOR_TYPES.items():
        entities.append(
            PstrykSensor(
                coordinator,
                sensor_type,
                sensor_info["name"],
                sensor_info["unit"],
                sensor_info["icon"],
            )
        )
    
    # Add hourly prices sensor
    entities.append(PstrykHourlyPricesSensor(coordinator))

    # Add current price template sensor
    # Hourly prices are in UTC, so we need to adjust for the timezone offset
    entities.append(
        PstrykTemplateSensor(
            hass,
            coordinator,
            "Current Electricity Price",
            "current_price",
            "{% set tz_offset = int(now().strftime('%z')[:3]) %}{{ states.sensor.today_s_electricity_prices.attributes.hourly_prices[(now() + timedelta(hours=tz_offset)).strftime('%Y-%m-%dT%H:00:00+00:00')] }}"
        )
    )

    # Add next hour price template sensor
    # Hourly prices are in UTC, so we need to adjust for the timezone offset
    entities.append(
        PstrykTemplateSensor(
            hass,
            coordinator,
            "Next Hour Electricity Price",
            "next_hour_price",
            "{% set tz_offset = int(now().strftime('%z')[:3]) %}{{ states.sensor.today_s_electricity_prices.attributes.hourly_prices[(now() + timedelta(hours=tz_offset+1)).strftime('%Y-%m-%dT%H:00:00+00:00')] }}"
        )
    )

    # Add is cheapest price sensor
    entities.append(PstrykIsCheapestSensor(coordinator))

    async_add_entities(entities)

class PstrykSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk sensor."""

    def __init__(self, coordinator, sensor_type, name, unit, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_type)

class PstrykHourlyPricesSensor(CoordinatorEntity, SensorEntity):
    """Sensor for today's electricity prices."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Electricity Prices"
        self._attr_unique_id = f"{DOMAIN}_today_prices"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_icon = "mdi:currency-usd"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None or "hourly_prices" not in self.coordinator.data:
            return {}
            
        return {
            "hourly_prices": self.coordinator.data.get("hourly_prices", {}),
            "prices_updated": self.coordinator.data.get("prices_updated"),
        }

    @property
    def native_value(self) -> None:
        """Return None as we don't need a state value."""
        return None
