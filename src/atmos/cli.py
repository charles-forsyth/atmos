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
    """
    pass


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def current(location_arg, location):
    """Get current weather conditions."""
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        weather = client.get_current_conditions(final_location)

        header_text = Text(f"Current Conditions: {final_location}", style="bold cyan")

        main_info = Table.grid(expand=True)
        main_info.add_column(justify="center")
        
        unit_label = "°F" if "FAHRENHEIT" in (weather.temperature.units or "").upper() else "°C"
        
        main_info.add_row(f"[bold active]{weather.temperature.value}{unit_label}[/bold active]")
        main_info.add_row(f"[italic]{weather.description}[/italic]")

        details = Table(show_header=False, box=box.SIMPLE, expand=True)
        details.add_column("Metric", style="dim")
        details.add_column("Value", style="bold")
        
        details.add_row("Feels Like", f"{weather.feels_like.value}{unit_label}")
        details.add_row("Wind", f"{weather.wind.speed} {weather.wind.direction}")
        details.add_row("Humidity", f"{weather.humidity}%")
        details.add_row("UV Index", str(weather.uv_index))
        details.add_row("Visibility", f"{weather.visibility}") 
        details.add_row("Pressure", f"{weather.pressure} hPa")

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


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--hours", default=24, help="Number of hours to look back (default: 24)")
def history(location_arg, location, hours):
    """
    Get historical weather data.
    """
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target
    
    try:
        console.print(f"[cyan]Fetching history for {final_location} (Last {hours} hours)...[/cyan]")
        history_items = client.get_hourly_history(final_location, hours=hours)
        
        if not history_items:
            console.print("[yellow]No history data returned.[/yellow]")
            return

        table = Table(title=f"History: {final_location}", box=box.SIMPLE_HEAD)
        table.add_column("Time", style="dim")
        table.add_column("Temp", style="bold cyan")
        table.add_column("Condition", style="white")
        table.add_column("Wind", style="green")
        table.add_column("Precip", style="blue")
        
        for item in history_items:
            # Format time: HH:MM
            time_str = item.timestamp.strftime("%H:%M")
            # If date changes? maybe show day too? For 24h, mostly ok.
            
            unit_label = "°F" if "FAHRENHEIT" in (item.temperature.units or "").upper() else "°C"
            temp_str = f"{item.temperature.value}{unit_label}"
            
            wind_str = f"{item.wind.speed} {item.wind.direction}"
            precip_str = f"{item.precipitation.probability}%"
            if item.precipitation.rate and item.precipitation.rate > 0:
                 precip_str += f" ({item.precipitation.rate})"
            
            table.add_row(time_str, temp_str, item.description, wind_str, precip_str)
            
        console.print(table)

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
