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
from homeassistant.helpers.template import Template, TemplateError

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

class PstrykTemplateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pstryk template sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        name: str,
        unique_id: str,
        template: str,
        *,
        device_class: SensorDeviceClass | None = SensorDeviceClass.MONETARY,
        native_unit_of_measurement: str | None = "PLN/kWh",
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._template = Template(template, hass)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{unique_id}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._hass = hass
        self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            return self._template.async_render()
        except (TemplateError, ValueError) as err:
            _LOGGER.error("Error rendering template: %s", err)
            return None

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
    
    # Add today's and tomorrow's rices sensor
    entities.append(PstrykTodaysPricesSensor(coordinator))
    entities.append(PstrykTomorrowsPricesSensor(coordinator))

    # Add current price template sensor
    # Hourly prices are in UTC, so we need to adjust for the timezone offset
    entities.append(
        PstrykTemplateSensor(
            hass,
            coordinator,
            "Current Electricity Price",
            "current_price",
            "{% set tz_offset = int(now().strftime('%z')[:3]) %}{{ states.sensor.today_s_electricity_prices.attributes.hourly_prices[(now() + timedelta(hours=-tz_offset)).strftime('%Y-%m-%dT%H:00:00+00:00')] }}",
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="PLN/kWh",
        )
    )

    # Add next hour price template sensor
    entities.append(
        PstrykTemplateSensor(
            hass,
            coordinator,
            "Next Hour Electricity Price",
            "next_hour_price",
            "{% set tz_offset = int(now().strftime('%z')[:3]) %}{{ states.sensor.today_s_electricity_prices.attributes.hourly_prices[(now() + timedelta(hours=-tz_offset+1)).strftime('%Y-%m-%dT%H:00:00+00:00')] }}",
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="PLN/kWh",
        )
    )

    # Add is cheapest price sensor
    entities.append(
        PstrykTemplateSensor(
            hass,
            coordinator,
            "Is Cheapest Electricity Price",
            "is_cheapest_electricity_price",
            "{% set cheapest_hour = states('sensor.today_s_cheapest_electricity_hour') %}{% if cheapest_hour != 'unavailable' and cheapest_hour != 'unknown' %}{% set cheapest_dt = as_datetime(cheapest_hour) %}{% set tz_offset = int(now().strftime('%z')[:3]) %}{{ 'on' if (cheapest_dt.hour - tz_offset) % 24 == now().hour else 'off' }}{% else %}{{ 'off' }}{% endif %}",
            device_class=None,
            native_unit_of_measurement=None,
        )
    )

    # Add cheapest hour sensor
    entities.append(
        PstrykSensor(
            coordinator,
            "today_cheapest_hour",
            "Today's Cheapest Electricity Hour",
            None,
            "mdi:clock-outline",
        )
    )

    # Add tomorrow's cheapest hour sensor
    entities.append(
        PstrykSensor(
            coordinator,
            "tomorrow_cheapest_hour",
            "Tomorrow's Cheapest Electricity Hour",
            None,
            "mdi:clock-outline",
        )
    )

    # Store entities reference
    hass.data[DOMAIN][entry.entry_id]["entities"] = entities
    
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
        
        # Set device class for timestamp sensors
        if sensor_type in ["today_cheapest_hour", "tomorrow_cheapest_hour"]:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_entity_registry_enabled_default = True
            self._attr_has_entity_name = True
            self._attr_entity_category = None
            self._attr_state_class = None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        # Get the value directly from coordinator data
        return self.coordinator.data.get(self._sensor_type)

class PstrykTodaysPricesSensor(CoordinatorEntity, SensorEntity):
    """Sensor for today's hourly electricity prices."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Today's Electricity Prices"
        self._attr_unique_id = f"{DOMAIN}_today_prices"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:currency-usd"
        self._attr_native_value = "off"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None or "today_prices" not in self.coordinator.data:
            return {}
            
        return {
            "hourly_prices": self.coordinator.data.get("today_prices", {}),
            "prices_updated": self.coordinator.data.get("prices_updated"),
        }

    @property
    def native_value(self):
        """Return on if we have prices, off otherwise."""
        if (self.coordinator.data is not None and 
            "today_prices" in self.coordinator.data and 
            self.coordinator.data["today_prices"]):
            return "on"
        return "off"
    
class PstrykTomorrowsPricesSensor(CoordinatorEntity, SensorEntity):
    """Sensor for tomorrow's hourly electricity prices."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Tomorrow's Electricity Prices"
        self._attr_unique_id = f"{DOMAIN}_tomorrow_prices"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_icon = "mdi:currency-usd"
        self._attr_native_value = "off"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None or "tomorrow_prices" not in self.coordinator.data:
            return {}
            
        return {
            "hourly_prices": self.coordinator.data.get("tomorrow_prices", {}),
            "prices_updated": self.coordinator.data.get("prices_updated"),
        }

    @property
    def native_value(self):
        """Return on if we have prices, off otherwise."""
        if (self.coordinator.data is not None and 
            "tomorrow_prices" in self.coordinator.data and 
            self.coordinator.data["tomorrow_prices"]):
            return "on"
        return "off"
