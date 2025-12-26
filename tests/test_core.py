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
    
    # The ACTUAL structure we discovered in debug
    mock_response.json.return_value = {
        "temperature": {"degrees": 15.5, "unit": "CELSIUS"},
        "feelsLikeTemperature": {"degrees": 14.0, "unit": "CELSIUS"},
        "relativeHumidity": 60.0,
        "weatherCondition": {
            "description": {"text": "Cloudy"},
            "type": "CLOUDY"
        },
        "wind": {
            "speed": {"value": 20.0, "unit": "KILOMETERS_PER_HOUR"},
            "direction": {"cardinal": "NE", "degrees": 45},
            "gust": {"value": 30.0, "unit": "KILOMETERS_PER_HOUR"}
        },
        "precipitation": {
            "probability": {"percent": 80.0, "type": "RAIN"},
            "qpf": {"quantity": 2.5, "unit": "MILLIMETERS"}
        },
        "uvIndex": 2,
        "visibility": {"distance": 16, "unit": "KILOMETERS"},
        "airPressure": {"meanSeaLevelMillibars": 1005.0}
    }
    mock_response.ok = True
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    weather = client.get_current_conditions("London")
    
    # Assert parsing
    assert isinstance(weather, CurrentConditions)
    assert weather.temperature.value == 15.5
    assert weather.description == "Cloudy"
    assert weather.wind.speed == 20.0
    assert weather.wind.direction == "NE"
    assert weather.precipitation.probability == 80.0
    assert weather.visibility == 16000.0 # 16 KM -> 16000 Meters
