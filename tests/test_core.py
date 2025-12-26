from atmos.core import AtmosClient
from atmos.models import HourlyHistoryItem

def test_get_coords(mocker):
    """Test the geocoding logic (mocked)."""
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

def test_get_history(mocker):
    """Test fetching history."""
    # Mock Geocode
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    
    # Mock API Response
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    
    # Simulated History Response (historyHours with interval)
    mock_response.json.return_value = {
        "historyHours": [
            {
                "interval": {"startTime": "2023-10-05T10:00:00Z"},
                "temperature": {"degrees": 50.0, "unit": "FAHRENHEIT"},
                "weatherCondition": {"description": {"text": "Rain"}, "type": "RAIN"},
                "wind": {"speed": {"value": 10}, "direction": {"cardinal": "N"}},
                "precipitation": {"probability": {"percent": 90}, "qpf": {"quantity": 0.5}}
            },
            {
                "interval": {"startTime": "2023-10-05T11:00:00Z"},
                "temperature": {"degrees": 52.0, "unit": "FAHRENHEIT"},
                "weatherCondition": {"description": {"text": "Cloudy"}},
                "wind": {"speed": {"value": 12}, "direction": {"cardinal": "NE"}}
            }
        ]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    history = client.get_hourly_history("London", hours=2)
    
    assert len(history) == 2
    assert isinstance(history[0], HourlyHistoryItem)
    assert history[0].temperature.value == 50.0
    assert history[0].timestamp.hour == 10
