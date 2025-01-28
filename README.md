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
  - Cheapest hour indicator
- Automatic daily price updates at 17:00
- Manual price update service
- Secure authentication with automatic token refresh


![|500](https://github.com/mateusz-orawczak/Home-Assistant-custom-components-Pstryk/blob/main/img/screen_1.jpg)
![|500](https://github.com/mateusz-orawczak/Home-Assistant-custom-components-Pstryk/blob/main/img/screen_2.jpg)

## Installation

### Manual Installation

1. Copy the `custom_components/pstryk` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration -> Integrations
4. Click the "+ ADD INTEGRATION" button
5. Search for "Pstryk"
6. Enter your email and password

## Configuration

The integration requires the following credentials:
- Email: Your Pstryk account email
- Password: Your Pstryk account password

## Available Sensors

The integration creates the following sensors:

| Sensor | Description | Unit | State |
|--------|-------------|------|-------|
| Today's Electricity Prices | Main sensor with today's hourly prices | - | on/off |
| Tomorrow's Electricity Prices | Main sensor with tomorrow's hourly prices | - | on/off |
| Current Electricity Price | Price for current hour | PLN/kWh | price |
| Next Hour Electricity Price | Price for next hour | PLN/kWh | price |
| Today's Average Electricity Price | Average price for today | PLN/kWh | price |
| Today's Cheapest Electricity Hour | Time when electricity is cheapest today | timestamp | time |
| Is Cheapest Electricity Price | Indicates if current hour is the cheapest | - | on/off |
| Today's Energy Usage | Energy consumed today | kWh | usage |
| Today's Energy Cost | Cost of energy consumed today | PLN | cost |
| This Week's Energy Usage | Energy consumed this week | kWh | usage |
| This Week's Energy Cost | Cost of energy consumed this week | PLN | cost |
| This Month's Energy Usage | Energy consumed this month | kWh | usage |
| This Month's Energy Cost | Cost of energy consumed this month | PLN | cost |

Both price sensors provide the following attributes:
- `hourly_prices`: Dictionary of hourly prices (UTC timestamps)
- `prices_updated`: Timestamp of the last price update

## Services

The integration provides the following service:

- `pstryk.update_prices`: Manually update electricity prices

## Automations

The integration automatically creates an automation to update prices daily at 17:00. Feel free to disable it if you don't need it, or change the time in the automation.

## Good to Know

Important implementation details that might be helpful to understand:

1. **WebSocket Periodic Reconnection**
   - The WebSocket connection is automatically reconnected every 3 hours
   - This is implemented to prevent data inconsistencies that occur with long-lasting connections to Pstryk's WebSocket server
   - You might notice brief disconnections in logs - this is expected behavior

2. **First Message Handling**
   - The first message received after establishing a WebSocket connection is intentionally ignored
   - This is because Pstryk initially sends cached (potentially outdated) data
   - This ensures that only fresh, accurate data is processed by the integration
   - Note that after Home Assistant restart, data may be unavailable for up to one minute while waiting for the first valid WebSocket message

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