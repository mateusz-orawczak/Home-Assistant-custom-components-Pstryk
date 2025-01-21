"""Constants for the Pstryk integration."""
from datetime import datetime, timedelta

DOMAIN = "pstryk"

# Configuration
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Get current date and time
TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_START = f"{TODAY}T00:00:00.000%2B01:00"
TODAY_END = f"{TODAY}T23:59:59.999%2B01:00"

# Get week start/end dates
WEEK_START_DATE = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
WEEK_END_DATE = (datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=6)).strftime('%Y-%m-%d')
WEEK_START = f"{WEEK_START_DATE}T00:00:00.000%2B01:00"
WEEK_END = f"{WEEK_END_DATE}T23:59:59.999%2B01:00"

# Get month start/end dates
MONTH_START_DATE = datetime.now().replace(day=1).strftime('%Y-%m-%d')
MONTH_END_DATE = ((datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
MONTH_START = f"{MONTH_START_DATE}T00:00:00.000%2B01:00"
MONTH_END = f"{MONTH_END_DATE}T23:59:59.999%2B01:00"

# API endpoints - replace with actual endpoints
API_BASE_URL = "https://api.pstryk.pl"
API_LOGIN_ENDPOINT = f"{API_BASE_URL}/auth/token/"
API_REFRESH_TOKEN_ENDPOINT = f"{API_BASE_URL}/auth/refresh"
API_ME_ENDPOINT = f"{API_BASE_URL}/api/me"

# These endpoints will be formatted with meter_id
API_TODAY_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-usage/?resolution=hour&window_start={TODAY_START}&window_end={TODAY_END}"
API_WEEK_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-usage/?resolution=week&window_start={WEEK_START}&window_end={WEEK_END}"
API_MONTH_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-usage/?resolution=month&window_start={MONTH_START}&window_end={MONTH_END}"
API_TODAY_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-cost/?resolution=hour&window_start={TODAY_START}&window_end={TODAY_END}"
API_WEEK_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-cost/?resolution=hour&window_start={WEEK_START}&window_end={WEEK_END}" # week resolution is not available in this endpoint
API_MONTH_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/{{meter_id}}/power-cost/?resolution=month&window_start={MONTH_START}&window_end={MONTH_END}"
API_PRICES_ENDPOINT = f"{API_BASE_URL}/api/pricing/?resolution=hour&window_start={TODAY_START}&window_end={TODAY_END}"

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
