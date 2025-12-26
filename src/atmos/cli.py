import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from atmos.core import client
from atmos.places import places_manager

console = Console()


class DefaultGroup(click.Group):
    """
    Custom Click Group that intercepts arguments.
    If the first argument is not a known command, it assumes it's a location
    and invokes the 'current' command with that location.
    """

    def parse_args(self, ctx, args):
        if not args:
            return super().parse_args(ctx, args)

        # If the first argument is a known command or help flag, proceed normally
        cmd_name = args[0]
        if cmd_name in self.commands or cmd_name in ctx.help_option_names:
            return super().parse_args(ctx, args)

        return super().parse_args(ctx, ["current"] + args)


@click.group(cls=DefaultGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="atmos")
def main():
    """
    Atmos: A professional CLI weather tool.

    Examples:
      atmos "New York"      # Get current weather
      atmos places add Home "123 Main St"
      atmos places list
    """
    pass


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def current(location_arg, location):
    """
    Get current weather conditions.

    Accepts location as a positional argument or via -L flag.
    """
    # Resolve location: Positional > Flag > Error
    target = location_arg or location
    if not target:
        console.print(
            "[bold red]Error:[/bold red] Missing location. Usage: [green]atmos <LOCATION>[/green]"
        )
        return

    # Check Address Book first
    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        weather = client.get_current_conditions(final_location)

        # --- UI Construction ---
        header_text = Text(f"Current Conditions: {final_location}", style="bold cyan")

        # Main Grid
        main_info = Table.grid(expand=True)
        main_info.add_column(justify="center")
        
        # Dynamic Unit Label
        unit_label = "°F" if "FAHRENHEIT" in (weather.temperature.units or "").upper() else "°C"
        
        main_info.add_row(f"[bold active]{weather.temperature.value}{unit_label}[/bold active]")
        main_info.add_row(f"[italic]{weather.description}[/italic]")

        # Details Table
        details = Table(show_header=False, box=box.SIMPLE, expand=True)
        details.add_column("Metric", style="dim")
        details.add_column("Value", style="bold")
        
        details.add_row("Feels Like", f"{weather.feels_like.value}{unit_label}")
        details.add_row("Wind", f"{weather.wind.speed} {weather.wind.direction}") # Units are complex now, just value+dir? Or use model logic? 
        # Actually API returns "MILES_PER_HOUR", maybe we should format that nicer?
        # For now, raw speed is fine, assuming user knows MPH if Temp is F.
        
        details.add_row("Humidity", f"{weather.humidity}%")
        details.add_row("UV Index", str(weather.uv_index))
        
        # Display raw visibility value (interpreted as standard units for now)
        details.add_row("Visibility", f"{weather.visibility}") 
        details.add_row("Pressure", f"{weather.pressure} hPa")

        # Layout
        content = Table.grid(expand=True, padding=(1, 2))
        content.add_column(ratio=1)
        content.add_column(ratio=1)
        content.add_row(
            Panel(main_info, title="Temperature", border_style="blue"),
            Panel(details, title="Details", border_style="green"),
        )

        console.print(Panel(content, title=header_text, border_style="cyan"))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# --- Places Management ---


@main.group()
def places():
    """Manage saved locations (Address Book)."""
    pass


@places.command("add")
@click.argument("name")
@click.argument("address")
def places_add(name, address):
    """Save a location."""
    places_manager.add(name, address)
    console.print(f"[green]Added:[/green] {name} -> {address}")


@places.command("list")
def places_list():
    """List all saved locations."""
    places = places_manager.list()
    if not places:
        console.print("[yellow]No places saved.[/yellow]")
        return

    table = Table(title="Saved Places", box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Address", style="white")

    for name, address in places.items():
        table.add_row(name, address)

    console.print(table)


@places.command("remove")
@click.argument("name")
def places_remove(name):
    """Remove a saved location."""
    if places_manager.remove(name):
        console.print(f"[green]Removed:[/green] {name}")
    else:
        console.print(f"[red]Place not found:[/red] {name}")


if __name__ == "__main__":
    main()