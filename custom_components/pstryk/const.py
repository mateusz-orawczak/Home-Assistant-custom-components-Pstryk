"""Constants for the Pstryk integration."""
DOMAIN = "pstryk"

# Configuration
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# API endpoints - replace with actual endpoints
API_BASE_URL = "https://api.pstryk.pl"
API_LOGIN_ENDPOINT = f"{API_BASE_URL}/auth/token/"
API_REFRESH_TOKEN_ENDPOINT = f"{API_BASE_URL}/auth/refresh"
API_TODAY_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-usage/?resolution=hour&window_start=2025-01-21T01:00:00.000Z&window_end=2025-01-21T22:59:59.999Z"
API_WEEK_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-usage/?resolution=week&window_start=2025-01-20T01:00:00.000Z&window_end=2025-01-26T22:59:59.999Z"
API_MONTH_USAGE_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-usage/?resolution=month&window_start=2025-01-01T01:00:00.000Z&window_end=2025-01-31T22:59:59.999Z"
API_TODAY_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-cost/?resolution=hour&window_start=2025-01-21T01:00:00.000Z&window_end=2025-01-21T22:59:59.999Z"
API_WEEK_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-cost/?resolution=week&window_start=2025-01-20T01:00:00.000Z&window_end=2025-01-26T22:59:59.999Z"
API_MONTH_COST_ENDPOINT = f"{API_BASE_URL}/api/meter-data/3019/power-cost/?resolution=month&window_start=2025-01-01T01:00:00.000Z&window_end=2025-01-31T22:59:59.999Z"
API_PRICES_ENDPOINT = f"{API_BASE_URL}/prices"

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
        "icon": "mdi:currency-pln",
    },
    "week_usage": {
        "name": "This Week's Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
    "week_cost": {
        "name": "This Week's Energy Cost",
        "unit": "PLN",
        "icon": "mdi:currency-pln",
    },
    "month_usage": {
        "name": "This Month's Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
    "month_cost": {
        "name": "This Month's Energy Cost",
        "unit": "PLN",
        "icon": "mdi:currency-pln",
    },
}
