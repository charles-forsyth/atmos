from atmos.core import AtmosClient
from atmos.models import WeatherAlert


def test_get_alerts(mocker):
    mocker.patch.object(AtmosClient, "get_coords", return_value=(40.7128, -74.0060))
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()

    # Simulated Alert Response
    mock_response.json.return_value = {
        "alerts": [
            {
                "headline": "Severe Thunderstorm Watch",
                "description": "Conditions are favorable for severe thunderstorms.",
                "severity": "SEVERE",
                "urgency": "IMMEDIATE",
                "certainty": "LIKELY",
                "event": "Severe Thunderstorm",
                "senderName": "NWS",
                "effective": "2023-10-06T12:00:00Z",
                "expires": "2023-10-06T18:00:00Z",
            }
        ]
    }
    mock_response.ok = True
    mock_get.return_value = mock_response

    client = AtmosClient()
    alerts = client.get_public_alerts("New York")

    assert len(alerts) == 1
    assert isinstance(alerts[0], WeatherAlert)
    assert alerts[0].type == "Severe Thunderstorm"
    assert alerts[0].severity == "SEVERE"
    assert alerts[0].start_time.year == 2023
