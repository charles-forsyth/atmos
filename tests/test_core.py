import pytest
from atmos.core import AtmosClient
from atmos.models import DailyForecastItem
from atmos.exceptions import AtmosAPIError


def test_get_coords(mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "status": "OK",
        "results": [{"geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}}],
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    client.api_key = "dummy"
    lat, lng = client.get_coords("New York")
    assert lat == 40.7128

    # Verify timeout argument was passed
    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs.get("timeout") == 10.0


def test_get_coords_zero_results(mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "ZERO_RESULTS", "results": []}
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    client.api_key = "dummy"

    with pytest.raises(ValueError) as excinfo:
        client.get_coords("NonexistentPlace12345")
    assert "Location not found" in str(excinfo.value)


def test_get_coords_request_denied(mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "status": "REQUEST_DENIED",
        "error_message": "The provided API key is invalid.",
        "results": [],
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    client.api_key = "dummy"

    with pytest.raises(AtmosAPIError) as excinfo:
        client.get_coords("New York")
    assert "Geocoding API Error (REQUEST_DENIED)" in str(excinfo.value)
    assert "The provided API key is invalid." in str(excinfo.value)
    assert excinfo.value.status_code == 200


def test_get_coords_over_query_limit(mocker):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "status": "OVER_QUERY_LIMIT",
        "error_message": "You have exceeded your daily request quota for this API.",
        "results": [],
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    client.api_key = "dummy"

    with pytest.raises(AtmosAPIError) as excinfo:
        client.get_coords("New York")
    assert "Geocoding API Error (OVER_QUERY_LIMIT)" in str(excinfo.value)
    assert "exceeded your daily request quota" in str(excinfo.value)


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
    client.api_key = "dummy"
    forecast = client.get_daily_forecast("London", days=1)

    assert len(forecast) == 1
    assert isinstance(forecast[0], DailyForecastItem)
    assert forecast[0].high_temp.value == 60.0
    assert forecast[0].description == "Sunny"
    assert forecast[0].sunrise.hour == 6

    # Verify timeout argument was passed in get_daily_forecast requests.get call
    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs.get("timeout") == 10.0


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
    client.api_key = "dummy"
    items = client.get_hourly_forecast("London", hours=1)

    assert len(items) == 1
    assert items[0].temperature.value == 55.0

    # Verify timeout argument was passed in get_hourly_forecast requests.get call
    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs.get("timeout") == 10.0
