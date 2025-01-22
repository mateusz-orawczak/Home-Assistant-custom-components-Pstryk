"""Constants for the Pstryk integration."""
from datetime import datetime, timedelta

DOMAIN = "pstryk"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_START = f"{TODAY}T00:00:00.000%2B01:00"
TOMORROW = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
TOMORROW_END = f"{TOMORROW}T23:59:59.999%2B01:00"

API_BASE_URL = "https://api.pstryk.pl"
API_LOGIN_ENDPOINT = f"{API_BASE_URL}/auth/token/"
API_REFRESH_TOKEN_ENDPOINT = f"{API_BASE_URL}/auth/token/refresh/"
API_METER_ENDPOINT = f"{API_BASE_URL}/api/meter"
API_PRICES_ENDPOINT = f"{API_BASE_URL}/api/pricing/?resolution=hour&window_start={TODAY_START}&window_end={TOMORROW_END}"
WS_ENDPOINT = "wss://api.pstryk.pl/ws/meter-data/{meter_id}/?timezone=Europe%2FWarsaw"

# Sensor names
SENSOR_TYPES = {
    "today_usage": {
        "name": "Today's Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
    "today_cost": {
        "name": "Today's Energy Cost",
        "unit": "PLN",
        "icon": "mdi:cash",
    },
    "week_usage": {
        "name": "This Week's Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
    "week_cost": {
        "name": "This Week's Energy Cost",
        "unit": "PLN",
        "icon": "mdi:cash",
    },
    "month_usage": {
        "name": "This Month's Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
    "month_cost": {
        "name": "This Month's Energy Cost",
        "unit": "PLN",
        "icon": "mdi:cash",
    },
}
