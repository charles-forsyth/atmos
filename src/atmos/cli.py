import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from atmos.core import client

console = Console()

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="atmos")
def main():
    """Atmos: A professional CLI weather tool."""
    pass

@main.command()
@click.option("-L", "--location", required=True, help="City or location name (e.g., 'New York')")
def current(location: str):
    """Get current weather conditions."""
    try:
        weather = client.get_current_conditions(location)
        
        # --- UI Construction ---
        
        # Header
        header_text = Text(f"Current Conditions: {location}", style="bold cyan")
        
        # Main Grid (Temperature & Desc)
        main_info = Table.grid(expand=True)
        main_info.add_column(justify="center")
        main_info.add_row(f"[bold active]{weather.temperature.value}°C[/bold active]")
        main_info.add_row(f"[italic]{weather.description}[/italic]")
        
        # Details Table
        details = Table(show_header=False, box=box.SIMPLE, expand=True)
        details.add_column("Metric", style="dim")
        details.add_column("Value", style="bold")
        
        details.add_row("Feels Like", f"{weather.feels_like.value}°C")
        details.add_row("Wind", f"{weather.wind.speed} km/h {weather.wind.direction}")
        details.add_row("Humidity", f"{weather.humidity}%")
        details.add_row("UV Index", str(weather.uv_index))
        details.add_row("Visibility", f"{weather.visibility/1000:.1f} km")
        details.add_row("Pressure", f"{weather.pressure} hPa")

        # Layout
        content = Table.grid(expand=True, padding=(1, 2))
        content.add_column(ratio=1)
        content.add_column(ratio=1)
        content.add_row(
            Panel(main_info, title="Temperature", border_style="blue"),
            Panel(details, title="Details", border_style="green")
        )

        console.print(Panel(content, title=header_text, border_style="cyan"))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()