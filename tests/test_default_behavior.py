from click.testing import CliRunner
from atmos.cli import main
from atmos.models import HourlyForecastItem, Temperature, Wind, Precipitation
from datetime import datetime


def test_default_behavior_no_args(mocker):
    # Mock the hourly forecast call which should be triggered by default
    mock_get = mocker.patch("atmos.core.client.get_hourly_forecast")

    mock_get.return_value = [
        HourlyForecastItem(
            timestamp=datetime(2023, 1, 1, 12, 0),
            temperature=Temperature(value=72.0, units="FAHRENHEIT"),
            feels_like=Temperature(value=70.0),
            description="Clear",
            wind=Wind(speed=5.0, direction="N"),
            precipitation=Precipitation(probability=0),
        )
    ]

    runner = CliRunner()
    result = runner.invoke(main, [])  # No args

    assert result.exit_code == 0

    # Verify it called the hourly forecast function
    mock_get.assert_called_once()

    # Verify arguments: Location="Home", hours=120 (5 days default * 24)
    args, kwargs = mock_get.call_args
    assert args[0] == "Home"
    # hours is passed as kwargs or positional depending on definition
    # client.get_hourly_forecast(location: str, hours: int = 24)
    # The command calls it with hours=days*24
    assert kwargs.get("hours") == 120 or args[1] == 120


def test_default_behavior_with_arg(mocker):
    # Should still map to 'current'
    mock_current = mocker.patch("atmos.core.client.get_current_conditions")
    mock_current.return_value = mocker.Mock(
        temperature=Temperature(value=20.0),
        feels_like=Temperature(value=18.0),
        description="Sunny",
        wind=Wind(speed=1, direction="N"),
        precipitation=Precipitation(),
        humidity=50,
        uv_index=1,
        visibility=10,
        pressure=1000,
    )

    runner = CliRunner()
    result = runner.invoke(main, ["London"])

    assert result.exit_code == 0
    mock_current.assert_called_once()
    assert mock_current.call_args[0][0] == "London"
