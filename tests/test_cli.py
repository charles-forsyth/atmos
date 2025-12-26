from click.testing import CliRunner
from atmos.cli import main
from atmos.models import CurrentConditions, Temperature, Wind, Precipitation

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
        pressure=1010.0
    )

def test_cli_current_positional(mocker):
    """Test 'atmos New York' (Default Command logic)."""
    mocker.patch("atmos.core.client.get_current_conditions", return_value=create_dummy_weather())
    
    runner = CliRunner()
    result = runner.invoke(main, ["New York"]) # Implicitly calls current
    
    assert result.exit_code == 0
    assert "Current Conditions: New York" in result.output

def test_cli_current_flag(mocker):
    """Test 'atmos current -L "New York"' (Explicit command)."""
    mocker.patch("atmos.core.client.get_current_conditions", return_value=create_dummy_weather())
    
    runner = CliRunner()
    result = runner.invoke(main, ["current", "-L", "New York"])
    
    assert result.exit_code == 0
    assert "Current Conditions: New York" in result.output

def test_cli_places_integration(mocker):
    """Test that 'atmos Home' resolves to the address."""
    mocker.patch("atmos.core.client.get_current_conditions", return_value=create_dummy_weather())
    
    # Mock PlacesManager.get to return an address for "Home"
    mocker.patch("atmos.places.places_manager.get", return_value="123 Main St")
    
    runner = CliRunner()
    result = runner.invoke(main, ["Home"])
    
    assert result.exit_code == 0
    # The output should show the RESOLVED address
    assert "Current Conditions: 123 Main St" in result.output

def test_cli_places_commands(mocker):
    """Test 'atmos places add/list/remove'."""
    # We mock the manager methods to avoid file I/O in CLI tests
    mock_add = mocker.patch("atmos.places.places_manager.add")
    mocker.patch("atmos.places.places_manager.list", return_value={"Work": "Office Addr"})
    mocker.patch("atmos.places.places_manager.remove", return_value=True)
    
    runner = CliRunner()
    
    # Add
    result = runner.invoke(main, ["places", "add", "Work", "Office Addr"])
    assert result.exit_code == 0
    assert "Added: Work" in result.output
    mock_add.assert_called_with("Work", "Office Addr")
    
    # List
    result = runner.invoke(main, ["places", "list"])
    assert result.exit_code == 0
    assert "Work" in result.output
    assert "Office Addr" in result.output
    
    # Remove
    result = runner.invoke(main, ["places", "remove", "Work"])
    assert result.exit_code == 0
    assert "Removed: Work" in result.output
