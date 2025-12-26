from click.testing import CliRunner
from atmos.cli import main

def test_cli_current():
    runner = CliRunner()
    result = runner.invoke(main, ["current"])
    assert result.exit_code == 0
    assert "Hello from Atmos!" in result.output
