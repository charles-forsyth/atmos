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
    """Test that we correctly parse the REAL API response structure."""
    
    # Mock Geocode
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    
    # Mock Weather API Response
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    
    # The ACTUAL structure we discovered in debug (Updated for Imperial)
    mock_response.json.return_value = {
        "temperature": {"degrees": 60.5, "unit": "FAHRENHEIT"},
        "feelsLikeTemperature": {"degrees": 58.0, "unit": "FAHRENHEIT"},
        "relativeHumidity": 60.0,
        "weatherCondition": {
            "description": {"text": "Cloudy"},
            "type": "CLOUDY"
        },
        "wind": {
            "speed": {"value": 12.0, "unit": "MILES_PER_HOUR"},
            "direction": {"cardinal": "NE", "degrees": 45},
            "gust": {"value": 20.0, "unit": "MILES_PER_HOUR"}
        },
        "precipitation": {
            "probability": {"percent": 10.0, "type": "RAIN"},
            "qpf": {"quantity": 0.1, "unit": "INCHES"}
        },
        "uvIndex": 2,
        "visibility": {"distance": 10, "unit": "MILES"},
        "airPressure": {"meanSeaLevelMillibars": 1005.0}
    }
    mock_response.ok = True
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    weather = client.get_current_conditions("London")
    
    # Assert parsing
    assert isinstance(weather, CurrentConditions)
    assert weather.temperature.value == 60.5
    assert weather.temperature.units == "FAHRENHEIT"
    assert weather.description == "Cloudy"
    
    # Assert parameters (Robustness Check)
    call_args = mock_get.call_args
    assert call_args is not None
    params = call_args[1]["params"]
    assert params["unitsSystem"] == "IMPERIAL"