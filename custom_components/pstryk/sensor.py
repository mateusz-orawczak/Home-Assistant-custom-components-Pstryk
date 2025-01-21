"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
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

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pstryk sensors."""
    api_client = hass.data[DOMAIN][entry.entry_id]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="pstryk",
        update_method=api_client.get_all_data,
        update_interval=timedelta(minutes=3),
    )

    await coordinator.async_config_entry_first_refresh()

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
        self._attr_name = "Today's Electricity Prices"
        self._attr_unique_id = f"{DOMAIN}_today_prices"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_icon = "mdi:currency-usd"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self):
        """Return the current price."""
        if self.coordinator.data is None or "current_price" not in self.coordinator.data:
            return None
        return self.coordinator.data["current_price"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None or "hourly_prices" not in self.coordinator.data:
            return {}
            
        return {
            "hourly_prices": self.coordinator.data["hourly_prices"],
            "next_hour_price": self.coordinator.data.get("next_hour_price"),
            "prices_updated": self.coordinator.data.get("prices_updated"),
        }
