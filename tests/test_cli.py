from click.testing import CliRunner
from atmos.cli import main
from atmos.models import CurrentConditions, Temperature, Wind, Precipitation

def test_cli_current(mocker):
    # Create a real-looking object
    dummy_weather = CurrentConditions(
        temperature=Temperature(value=20.0),
        feels_like=Temperature(value=18.0),
        humidity=50.0,
        description="Test Sunny",
        wind=Wind(speed=10.0, direction="N"),
        precipitation=Precipitation(),
        uv_index=3,
        visibility=10000.0,
        pressure=1010.0
    )

    # Mock the client to return this object
    mocker.patch("atmos.core.client.get_current_conditions", return_value=dummy_weather)
    
    runner = CliRunner()
    result = runner.invoke(main, ["current", "-L", "New York"])
    
    # Debug output if it fails
    if result.exit_code != 0:
        print(result.output)

    assert result.exit_code == 0
    assert "Current Conditions" in result.output
    assert "20.0°C" in result.output
