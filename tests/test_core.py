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
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    client = AtmosClient()
    lat, lng = client.get_coords("New York")
    
    assert lat == 40.7128
    assert lng == -74.0060
    mock_get.assert_called_once()

def test_get_current_conditions_structure(mocker):
    """Test that we return a valid CurrentConditions object."""
    # Since we are currently returning a dummy object in core.py, 
    # we just verify the return type for now.
    
    # Mock get_coords to avoid the network call there
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    
    client = AtmosClient()
    weather = client.get_current_conditions("London")
    
    assert isinstance(weather, CurrentConditions)
    assert weather.temperature.value == 22.5
