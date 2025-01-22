# Home Assistant Pstryk Integration

This custom integration for Home Assistant allows you to monitor your energy usage and costs directly from Pstryk. It provides real-time data about your energy consumption, associated costs for different time periods, and today's electricity prices.

## Features

- Real-time energy usage monitoring
- Automatic data updates every 3 minutes
- Multiple time period tracking:
  - Today's usage and cost
  - This week's usage and cost
  - This month's usage and cost
- Today's electricity prices with hourly breakdown
- Secure authentication

## Installation

### Manual Installation

1. Copy the `custom_components/pstryk` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration -> Integrations
4. Click the "+ ADD INTEGRATION" button
5. Search for "Pstryk"
6. Enter your email and password

### HACS Installation

*Coming soon*

## Configuration

The integration requires the following credentials:
- Email: Your Pstryk account email
- Password: Your Pstryk account password

## Available Sensors

The integration creates the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| Today's Energy Usage | Energy consumed today | kWh |
| Today's Energy Cost | Cost of energy consumed today | PLN |
| This Week's Energy Usage | Energy consumed this week | kWh |
| This Week's Energy Cost | Cost of energy consumed this week | PLN |
| This Month's Energy Usage | Energy consumed this month | kWh |
| This Month's Energy Cost | Cost of energy consumed this month | PLN |
| Today's Electricity Prices | Hourly electricity prices | PLN/kWh |

The "Today's Electricity Prices" sensor provides the following attributes:
- `hourly_prices`: Dictionary of hourly prices for today
- `prices_updated`: Timestamp of the last price update

## Troubleshooting

Common issues and their solutions:

1. **Authentication Failed**
   - Verify your email and password are correct
   - Ensure your account is active with Pstryk

2. **No Data Available**
   - Check your internet connection
   - Verify your Pstryk API is accessible
   - Check the Home Assistant logs for detailed error messages

## Contributing

Feel free to contribute to this project by:
1. Reporting bugs
2. Suggesting enhancements
3. Creating pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is not officially associated with or endorsed by Pstryk. Use at your own risk. 