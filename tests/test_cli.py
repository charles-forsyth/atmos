from click.testing import CliRunner
from atmos.cli import main
from atmos.models import (
    CurrentConditions,
    Temperature,
    Wind,
    Precipitation,
    HourlyForecastItem,
    DailyForecastItem,
)
from datetime import datetime


def create_dummy_weather():
    return CurrentConditions(
        temperature=Temperature(value=20.0),
        feels_like=Temperature(value=18.0),
        humidity=50.0,
        description="Test Sunny",
        wind=Wind(speed=10.0, direction="N"),
        precipitation=Precipitation(),
        uv_index=3,
        visibility=10000.0,
        pressure=1010.0,
    )


def test_cli_current_positional(mocker):
    mocker.patch(
        "atmos.core.client.get_current_conditions", return_value=create_dummy_weather()
    )
    runner = CliRunner()
    result = runner.invoke(main, ["New York"])
    assert result.exit_code == 0
    assert "Current: New York" in result.output


def test_cli_current_flag(mocker):
    mocker.patch(
        "atmos.core.client.get_current_conditions", return_value=create_dummy_weather()
    )
    runner = CliRunner()
    result = runner.invoke(main, ["current", "-L", "New York"])
    assert result.exit_code == 0
    assert "Current: New York" in result.output


def test_cli_places_integration(mocker):
    mocker.patch(
        "atmos.core.client.get_current_conditions", return_value=create_dummy_weather()
    )
    mocker.patch("atmos.places.places_manager.get", return_value="123 Main St")
    runner = CliRunner()
    result = runner.invoke(main, ["Home"])
    assert result.exit_code == 0
    assert "Current: 123 Main St" in result.output


def test_cli_places_commands(mocker):
    mock_add = mocker.patch("atmos.places.places_manager.add")
    mocker.patch(
        "atmos.places.places_manager.list", return_value={"Work": "Office Addr"}
    )
    mocker.patch("atmos.places.places_manager.remove", return_value=True)
    runner = CliRunner()
    result = runner.invoke(main, ["places", "add", "Work", "Office Addr"])
    assert result.exit_code == 0
    assert "Added: Work" in result.output
    mock_add.assert_called_with("Work", "Office Addr")
    result = runner.invoke(main, ["places", "list"])
    assert result.exit_code == 0
    assert "Work" in result.output
    result = runner.invoke(main, ["places", "remove", "Work"])
    assert result.exit_code == 0
    assert "Removed: Work" in result.output


def test_cli_graph(mocker):
    """Test graph command."""
    mock_forecast = mocker.patch("atmos.core.client.get_hourly_forecast")
    items = []
    for i in range(5):
        items.append(
            HourlyForecastItem(
                timestamp=datetime(2023, 10, 6, 12 + i),
                temperature=Temperature(value=20.0 + i),
                feels_like=Temperature(),
                wind=Wind(),
                precipitation=Precipitation(),
            )
        )
    mock_forecast.return_value = items
    runner = CliRunner()
    result = runner.invoke(main, ["graph", "-L", "London", "--hours", "5"])
    assert result.exit_code == 0
    assert "Temp Trend" in result.output


def test_cli_find(mocker):
    """Test find command."""
    mock_daily = mocker.patch("atmos.core.client.get_daily_forecast")

    # Create dummy daily items
    items = []
    items.append(
        DailyForecastItem(
            date=datetime(2023, 10, 6),
            low_temp=Temperature(value=60.0, units="FAHRENHEIT"),
            high_temp=Temperature(value=75.0, units="FAHRENHEIT"),
            description="Sunny",
            precipitation_probability=0.0,
        )
    )
    # Bad day
    items.append(
        DailyForecastItem(
            date=datetime(2023, 10, 7),
            low_temp=Temperature(value=50.0, units="FAHRENHEIT"),
            high_temp=Temperature(value=55.0, units="FAHRENHEIT"),
            description="Rain",
            precipitation_probability=80.0,
        )
    )

    mock_daily.return_value = items

    runner = CliRunner()
    result = runner.invoke(main, ["find", "-L", "London", "--activity", "hiking"])

    assert result.exit_code == 0
    assert "Best Days for Hiking" in result.output
    # Should recommend the first day (Sunny)
    assert "100/100" in result.output
    # Should penalize second day
    assert "High rain chance" in result.output
