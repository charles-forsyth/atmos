import requests
from atmos.core import AtmosClient
from atmos.cache import cache_manager
from atmos.models import CurrentConditions, HourlyForecastItem


def test_get_coords_offline_fallback(mocker):
    """Test that get_coords falls back to cached values when the network call fails."""
    # Ensure cache is clear and set an expired coordinate entry
    cache_manager.clear()
    loc_key = "coords_springfield"
    cache_manager.set(
        loc_key, (39.7817, -89.6501), expires_sec=-1
    )  # expires immediately

    # Mock requests.get to fail
    mocker.patch("requests.get", side_effect=requests.RequestException("No internet"))

    # Mock Console.print to assert the yellow warning is printed
    mock_print = mocker.patch("atmos.core.console.print")

    client = AtmosClient()
    client.api_key = "dummy"

    # Call method
    lat, lng = client.get_coords("Springfield")

    # Verify fallback to cached coordinates
    assert lat == 39.7817
    assert lng == -89.6501

    # Verify warning message was printed
    mock_print.assert_called_once()
    args, _ = mock_print.call_args
    assert "Geocoding connection failed. Using cached coordinates" in args[0]


def test_get_current_conditions_offline_fallback(mocker):
    """Test get_current_conditions falls back to expired cached data during network failure."""
    cache_manager.clear()

    # Set coordinates in cache so lookup doesn't need API call
    cache_manager.set("coords_springfield", (39.7817, -89.6501), expires_sec=3600)

    # Set current weather in cache
    mock_current = {
        "temperature": {"value": 72.0, "units": "FAHRENHEIT"},
        "feels_like": {"value": 74.0, "units": "FAHRENHEIT"},
        "humidity": 60.0,
        "description": "Scattered Clouds",
        "wind": {"speed": 10.0, "direction": "SW", "gust": 15.0},
        "precipitation": {"type": "None", "rate": 0.0, "probability": 0.0},
        "uv_index": 3,
        "visibility": 10.0,
        "pressure": 1015.0,
    }

    # Set as expired cache entry
    cache_manager.set("current_39.7817_-89.6501", mock_current, expires_sec=-1)

    # Mock requests.get to fail
    mocker.patch("requests.get", side_effect=requests.RequestException("API Down"))
    mock_print = mocker.patch("atmos.core.console.print")

    client = AtmosClient()
    client.api_key = "dummy"

    # Fetch
    res = client.get_current_conditions("Springfield")

    assert isinstance(res, CurrentConditions)
    assert res.temperature.value == 72.0
    assert res.description == "Scattered Clouds"

    # Verify yellow warning was logged
    mock_print.assert_called_once()
    args, _ = mock_print.call_args
    assert "Using cached current conditions" in args[0]


def test_get_hourly_forecast_by_coords_offline_fallback(mocker):
    """Test get_hourly_forecast_by_coords offline fallback logic."""
    cache_manager.clear()

    mock_hourly = [
        {
            "timestamp": "2023-10-06T12:00:00+00:00",
            "temperature": {"value": 68.0, "units": "FAHRENHEIT"},
            "feels_like": {"value": 68.0, "units": "FAHRENHEIT"},
            "humidity": 50.0,
            "description": "Clear",
            "wind": {"speed": 5.0, "direction": "N", "gust": 5.0},
            "precipitation": {"type": "None", "rate": 0.0, "probability": 0.0},
            "pressure": 1013.25,
        }
    ]

    cache_manager.set("hourly_39.7817_-89.6501_24", mock_hourly, expires_sec=-1)

    mocker.patch("requests.get", side_effect=requests.RequestException("Offline"))
    mock_print = mocker.patch("atmos.core.console.print")

    client = AtmosClient()
    client.api_key = "dummy"

    res = client.get_hourly_forecast_by_coords(39.7817, -89.6501, hours=24)

    assert len(res) == 1
    assert isinstance(res[0], HourlyForecastItem)
    assert res[0].temperature.value == 68.0

    mock_print.assert_called_once()
    args, _ = mock_print.call_args
    assert "Using cached hourly forecast" in args[0]


def test_get_route_directions_offline_fallback(mocker):
    """Test get_route_directions offline fallback logic."""
    cache_manager.clear()

    mock_directions = {
        "status": "OK",
        "routes": [
            {
                "legs": [
                    {
                        "start_location": {"lat": 1.0, "lng": 2.0},
                        "end_location": {"lat": 3.0, "lng": 4.0},
                        "steps": [],
                    }
                ]
            }
        ],
    }

    cache_manager.set("route_a_b", mock_directions, expires_sec=-1)

    mocker.patch("requests.get", side_effect=requests.RequestException("Offline"))
    mock_print = mocker.patch("atmos.core.console.print")

    client = AtmosClient()
    client.api_key = "dummy"

    res = client.get_route_directions("A", "B")
    assert res == mock_directions

    mock_print.assert_called_once()
    args, _ = mock_print.call_args
    assert "Using cached route" in args[0]
