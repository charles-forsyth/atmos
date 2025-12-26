import click
from rich.console import Console

console = Console()

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="atmos")
def main():
    """Atmos: A professional CLI weather tool."""
    pass

@main.command()
def current():
    """Get current weather."""
    console.print("[bold green]Hello from Atmos![/bold green]")

if __name__ == "__main__":
    main()
