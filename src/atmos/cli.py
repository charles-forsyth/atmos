import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
import asciichartpy

from atmos.core import client
from atmos.places import places_manager
from atmos.utils import get_stargazing_conditions

console = Console()

def format_dt(dt: datetime) -> str:
    local_dt = dt.astimezone() 
    return local_dt.strftime("%H:%M")

def format_date(dt: datetime) -> str:
    local_dt = dt.astimezone()
    return local_dt.strftime("%a %b %d")

class DefaultGroup(click.Group):
    def parse_args(self, ctx, args):
        if not args:
            return super().parse_args(ctx, args)
        cmd_name = args[0]
        if cmd_name in self.commands or cmd_name in ctx.help_option_names:
            return super().parse_args(ctx, args)
        return super().parse_args(ctx, ["current"] + args)


@click.group(cls=DefaultGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="atmos")
def main():
    """Atmos: A professional CLI weather tool."""
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
    """Get historical weather data."""
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
            time_str = format_dt(item.timestamp)
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

@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--days", default=5, help="Number of days (default: 5)")
@click.option("--hourly", is_flag=True, help="Show hourly forecast instead of daily")
def forecast(location_arg, location, days, hourly):
    """Get weather forecast."""
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target
    
    try:
        if hourly:
            console.print(f"[cyan]Fetching hourly forecast for {final_location}...[/cyan]")
            items = client.get_hourly_forecast(final_location, hours=days*24) 
            
            table = Table(title=f"Hourly Forecast: {final_location}", box=box.SIMPLE_HEAD)
            table.add_column("Time", style="dim")
            table.add_column("Temp", style="bold cyan")
            table.add_column("Condition", style="white")
            table.add_column("Wind", style="green")
            table.add_column("Precip", style="blue")
            
            for item in items:
                time_str = format_dt(item.timestamp)
                unit_label = "°F" if "FAHRENHEIT" in (item.temperature.units or "").upper() else "°C"
                temp_str = f"{item.temperature.value}{unit_label}"
                wind_str = f"{item.wind.speed} {item.wind.direction}"
                precip_str = f"{item.precipitation.probability}%"
                
                table.add_row(time_str, temp_str, item.description, wind_str, precip_str)
            console.print(table)
            
        else:
            console.print(f"[cyan]Fetching daily forecast for {final_location} ({days} days)...[/cyan]")
            items = client.get_daily_forecast(final_location, days=days)
            
            table = Table(title=f"Daily Forecast: {final_location}", box=box.SIMPLE_HEAD)
            table.add_column("Date", style="dim")
            table.add_column("High/Low", style="bold cyan")
            table.add_column("Condition", style="white")
            table.add_column("Precip", style="blue")
            table.add_column("Sun", style="yellow")
            
            for item in items:
                date_str = format_date(item.date)
                unit_label = "°F" if "FAHRENHEIT" in (item.high_temp.units or "").upper() else "°C"
                temp_str = f"{item.high_temp.value}{unit_label} / {item.low_temp.value}{unit_label}"
                
                sun_str = ""
                if item.sunrise and item.sunset:
                    sun_str = f"☀ {format_dt(item.sunrise)} ↓ {format_dt(item.sunset)}"
                
                table.add_row(date_str, temp_str, item.description, f"{item.precipitation_probability}%", sun_str)
            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def alert(location_arg, location):
    """Check for severe weather alerts."""
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target
    
    try:
        console.print(f"[cyan]Checking for active alerts in {final_location}...[/cyan]")
        alerts = client.get_public_alerts(final_location)
        
        if not alerts:
            console.print("[bold green]✓ No active weather alerts.[/bold green]")
            return
            
        for a in alerts:
            style = "bold red" if a.severity in ["SEVERE", "EXTREME"] else "bold yellow"
            panel = Panel(
                f"[bold]{a.headline}[/bold]\n\n{a.description}",
                title=f"[{style}]{a.type} ({a.severity})[/{style}]",
                subtitle=f"Source: {a.source}",
                border_style="red"
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--hours", default=24, help="Number of hours to graph (default: 24)")
@click.option("--metric", default="temp", type=click.Choice(['temp', 'precip', 'wind']), help="Metric to graph")
def graph(location_arg, location, hours, metric):
    """Visualize weather trends (ASCII Graph)."""
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target
    
    try:
        console.print(f"[cyan]Fetching forecast for {final_location}...[/cyan]")
        items = client.get_hourly_forecast(final_location, hours=hours)
        
        if not items:
            console.print("[yellow]No data available.[/yellow]")
            return
            
        series = []
        labels = []
        
        for i, item in enumerate(items):
            val = 0.0
            if metric == 'temp':
                val = item.temperature.value or 0.0
            elif metric == 'precip':
                val = item.precipitation.probability or 0.0
            elif metric == 'wind':
                val = item.wind.speed or 0.0
            
            series.append(val)
            if i % 4 == 0:
                labels.append(format_dt(item.timestamp))
            else:
                labels.append("")

        console.print(f"\n[bold]{metric.title()} Trend ({hours}h)[/bold]")
        
        cfg = {"height": 15, "format": "{:8.1f}"}
        if metric == 'temp':
            cfg["colors"] = [asciichartpy.red]
        elif metric == 'precip':
            cfg["colors"] = [asciichartpy.blue]
        
        chart = asciichartpy.plot(series, cfg)
        console.print(Text.from_ansi(chart))
        
        start_t = format_dt(items[0].timestamp)
        end_t = format_dt(items[-1].timestamp)
        console.print(f"[dim]Time: {start_t} -> {end_t}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def stars(location_arg, location):
    """Astronomy info and stargazing forecast."""
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target
    
    try:
        # Get today's forecast for astronomy data
        console.print(f"[cyan]Fetching astronomy data for {final_location}...[/cyan]")
        items = client.get_daily_forecast(final_location, days=1)
        if not items:
            console.print("[yellow]No data.[/yellow]")
            return
            
        today = items[0]
        
        # Stargazing logic
        condition_report = get_stargazing_conditions(today.cloud_cover or 0, today.moon_phase or "Unknown")
        
        # UI
        grid = Table.grid(expand=True, padding=(1, 2))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        
        # Sun Panel
        sun_table = Table(show_header=False, box=None)
        sun_table.add_row("Rise", format_dt(today.sunrise) if today.sunrise else "-")
        sun_table.add_row("Set", format_dt(today.sunset) if today.sunset else "-")
        
        # Moon Panel
        moon_table = Table(show_header=False, box=None)
        moon_table.add_row("Phase", today.moon_phase.replace("_", " ").title())
        moon_table.add_row("Rise", format_dt(today.moonrise) if today.moonrise else "-")
        moon_table.add_row("Set", format_dt(today.moonset) if today.moonset else "-")
        
        grid.add_row(
            Panel(sun_table, title="☀ Sun", border_style="yellow"),
            Panel(moon_table, title="☾ Moon", border_style="white")
        )
        
        # Condition Panel
        cond_panel = Panel(
            f"Cloud Cover: {today.cloud_cover}%\n\n[bold]{condition_report}[/bold]",
            title="✨ Stargazing Forecast",
            border_style="blue"
        )
        
        main_layout = Table.grid(expand=True)
        main_layout.add_row(grid)
        main_layout.add_row(cond_panel)
        
        console.print(Panel(main_layout, title=f"Astronomy: {final_location}", border_style="magenta"))

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
