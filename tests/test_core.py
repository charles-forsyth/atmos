from atmos.core import AtmosClient
from atmos.models import CurrentConditions

def test_get_coords(mocker):
    """Test the geocoding logic (mocked)."""
    mock_get = mocker.patch("requests.get")
    
    # Mock Response
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "geometry": {
                    "location": {"lat": 40.7128, "lng": -74.0060}
                }
            }
        ]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    lat, lng = client.get_coords("New York")
    
    assert lat == 40.7128
    assert lng == -74.0060

def test_get_current_conditions_live_structure(mocker):
    """Test that we correctly parse a 'real' (mocked) API response."""
    
    # Mock Geocode
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    
    # Mock Weather API Response
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    
    mock_response.json.return_value = {
        "currentConditions": {
            "temperature": {"value": 15.5, "units": "CELSIUS"},
            "feelsLikeTemperature": {"value": 14.0, "units": "CELSIUS"},
            "humidity": 60.0,
            "conditionDescription": "Cloudy",
            "wind": {"speed": 20.0, "direction": "NE", "gust": 30.0},
            "precipitation": {"type": "Rain", "rate": 2.5, "probability": 80.0},
            "uvIndex": 2,
            "visibility": 8000.0,
            "pressure": 1005.0
        }
    }
    mock_response.ok = True
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    weather = client.get_current_conditions("London")
    
    # Assert parsing
    assert isinstance(weather, CurrentConditions)
    assert weather.temperature.value == 15.5
    
    # Assert parameters (Robustness Check)
    call_args = mock_get.call_args
    assert call_args is not None
    # args[0] is url, args[1] is kwargs (params)
    params = call_args[1]["params"]
    assert "location.latitude" in params
    assert "location.longitude" in params
    assert "unitsSystem" in params