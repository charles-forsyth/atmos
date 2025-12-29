from atmos.core import AtmosClient
from atmos.models import DailyForecastItem


def test_get_coords(mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": [{"geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}}]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    lat, lng = client.get_coords("New York")
    assert lat == 40.7128


def test_get_forecast(mocker):
    """Test fetching daily forecast."""
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()

    # Simulated Forecast Response
    mock_response.json.return_value = {
        "forecastDays": [
            {
                "interval": {"startTime": "2023-10-06T00:00:00Z"},
                "maxTemperature": {"degrees": 60.0, "unit": "FAHRENHEIT"},
                "minTemperature": {"degrees": 40.0, "unit": "FAHRENHEIT"},
                "daytimeForecast": {
                    "weatherCondition": {"description": {"text": "Sunny"}},
                    "precipitation": {"probability": {"percent": 10}},
                },
                "sunEvents": {
                    "sunriseTime": "2023-10-06T06:00:00Z",
                    "sunsetTime": "2023-10-06T18:00:00Z",
                },
            }
        ]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    forecast = client.get_daily_forecast("London", days=1)

    assert len(forecast) == 1
    assert isinstance(forecast[0], DailyForecastItem)
    assert forecast[0].high_temp.value == 60.0
    assert forecast[0].description == "Sunny"
    assert forecast[0].sunrise.hour == 6


def test_get_hourly_forecast(mocker):
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()

    # Simulated Hourly Response
    mock_response.json.return_value = {
        "forecastHours": [
            {
                "interval": {"startTime": "2023-10-06T12:00:00Z"},
                "temperature": {"degrees": 55.0},
                "weatherCondition": {"description": {"text": "Cloudy"}},
            }
        ]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    items = client.get_hourly_forecast("London", hours=1)

    assert len(items) == 1
    assert items[0].temperature.value == 55.0
