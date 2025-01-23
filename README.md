# Home Assistant Pstryk Integration

This custom integration for Home Assistant allows you to monitor your energy usage and costs directly from Pstryk. It provides real-time data about your energy consumption, associated costs for different time periods, and electricity prices.

## Features

- Real-time energy usage monitoring via WebSocket connection
- Automatic data updates
- Multiple time period tracking:
  - Today's usage and cost
  - This week's usage and cost
  - This month's usage and cost
- Electricity price monitoring:
  - Current hour price
  - Next hour price
  - Average daily price
  - Is current price the cheapest?
- Automatic daily price updates at 17:00
- Manual price update service
- Secure authentication with automatic token refresh

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
| Electricity Prices | Main sensor with hourly prices | PLN/kWh |
| Current Electricity Price | Price for current hour | PLN/kWh |
| Next Hour Electricity Price | Price for next hour | PLN/kWh |
| Today's Average Electricity Price | Average price for today | PLN/kWh |
| Is Cheapest Electricity Price | Indicates if current price is lowest | on/off |
| Today's Energy Usage | Energy consumed today | kWh |
| Today's Energy Cost | Cost of energy consumed today | PLN |
| This Week's Energy Usage | Energy consumed this week | kWh |
| This Week's Energy Cost | Cost of energy consumed this week | PLN |
| This Month's Energy Usage | Energy consumed this month | kWh |
| This Month's Energy Cost | Cost of energy consumed this month | PLN |

The "Electricity Prices" sensor provides the following attributes:
- `hourly_prices`: Dictionary of hourly prices for today
- `prices_updated`: Timestamp of the last price update

## Services

The integration provides the following service:

- `pstryk.update_prices`: Manually update electricity prices

## Automations

The integration automatically creates an automation to update prices daily at 17:00. Feel free to disable it if you don't need it, or change the time in the automation.

## Troubleshooting

Common issues and their solutions:

1. **Authentication Failed**
   - Verify your email and password are correct
   - Ensure your account is active with Pstryk

2. **No Data Available**
   - Check your internet connection
   - Verify your Pstryk API is accessible
   - Check the Home Assistant logs for detailed error messages

3. **WebSocket Disconnections**
   - The integration will automatically attempt to reconnect with exponential backoff
   - Token refresh is handled automatically
   - Check logs for detailed connection status

## Contributing

Feel free to contribute to this project by:
1. Reporting bugs
2. Suggesting enhancements
3. Creating pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is not officially associated with or endorsed by Pstryk. Use at your own risk.