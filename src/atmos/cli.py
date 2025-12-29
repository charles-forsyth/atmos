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
from atmos.evaluator import SuitabilityEvaluator
from atmos.exceptions import AtmosAPIError

console = Console()


def format_dt(dt: datetime) -> str:
    local_dt = dt.astimezone()
    return local_dt.strftime("%H:%M")


def format_time_ampm(dt: datetime) -> str:
    """Formats time as 07:18 AM."""
    local_dt = dt.astimezone()
    return local_dt.strftime("%I:%M %p")


def format_date(dt: datetime) -> str:
    local_dt = dt.astimezone()
    return local_dt.strftime("%a %b %d")


class DefaultGroup(click.Group):
    def parse_args(self, ctx, args):
        if not args:
            return super().parse_args(ctx, ["forecast", "-L", "Home", "--hourly"])
        cmd_name = args[0]
        if cmd_name in self.commands or cmd_name in ctx.help_option_names:
            return super().parse_args(ctx, args)
        return super().parse_args(ctx, ["current"] + args)


@click.group(cls=DefaultGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="atmos")
def main():
    """
    Atmos: A professional CLI weather tool.

    Powered by Google Maps Platform Weather API.

    \b
    EXAMPLES:
      atmos "New York"              # Current weather
      atmos forecast -L "London"    # 5-day forecast
      atmos graph --hours 24        # Temperature trend graph
      atmos stars                   # Astronomy & Stargazing info
      atmos find --activity hiking  # Find best days to hike
      atmos alert                   # Check for severe weather alerts
    """
    pass


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def current(location_arg, location):
    """
    Get current weather conditions.

    The default command. You can omit 'current' and just type the location.

    \b
    EXAMPLES:
      atmos "San Francisco"
      atmos current -L "Tokyo"
    """
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        weather = client.get_current_conditions(final_location)

        # Main Layout Grid
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column()
        grid.add_column()

        # Left Column: Temperature & Condition
        unit_label = (
            "°F" if "FAHRENHEIT" in (weather.temperature.units or "").upper() else "°C"
        )
        left_table = Table.grid(padding=(0, 1))
        left_table.add_column(justify="center")

        # Big Temp
        left_table.add_row(
            f"[bold cyan size=3]{weather.temperature.value}{unit_label}[/bold cyan size=3]"
        )
        # Condition
        left_table.add_row(f"[italic]{weather.description}[/italic]")
        # Feels Like
        left_table.add_row(
            f"[dim]Feels like {weather.feels_like.value}{unit_label}[/dim]"
        )

        # Right Column: Details
        right_table = Table.grid(padding=(0, 1))
        right_table.add_column(style="bold white", width=12)
        right_table.add_column()

        right_table.add_row("Wind:", f"{weather.wind.speed} {weather.wind.direction}")
        right_table.add_row("Humidity:", f"{weather.humidity}%")
        right_table.add_row("UV Index:", str(weather.uv_index))
        right_table.add_row("Visibility:", f"{weather.visibility}")
        right_table.add_row("Pressure:", f"{weather.pressure} hPa")

        # Add to main grid
        grid.add_row(left_table, right_table)

        console.print(
            Panel(
                grid,
                title=f"Current: {final_location}",
                border_style="cyan",
                expand=False,
            )
        )

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--hours", default=24, help="Number of hours to look back (default: 24)")
def history(location_arg, location, hours):
    """
    Get historical weather data.

    Shows hourly data for the past N hours (default 24).

    \b
    EXAMPLES:
      atmos history -L "Seattle"
      atmos history --hours 12
    """
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        console.print(
            f"[cyan]Fetching history for {final_location} (Last {hours} hours)...[/cyan]"
        )
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
            unit_label = (
                "°F" if "FAHRENHEIT" in (item.temperature.units or "").upper() else "°C"
            )
            temp_str = f"{item.temperature.value}{unit_label}"

            wind_str = f"{item.wind.speed} {item.wind.direction}"
            precip_str = f"{item.precipitation.probability}%"
            if item.precipitation.rate and item.precipitation.rate > 0:
                precip_str += f' ({item.precipitation.rate}")'

            table.add_row(time_str, temp_str, item.description, wind_str, precip_str)

        console.print(table)

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--days", default=5, help="Number of days (default: 5)")
@click.option("--hourly", is_flag=True, help="Show hourly forecast instead of daily")
def forecast(location_arg, location, days, hourly):
    """
    Get weather forecast.

    Shows daily summary by default, or hourly details with --hourly.

    \b
    EXAMPLES:
      atmos forecast -L "Paris"
      atmos forecast --days 10
      atmos forecast --hourly
    """
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        if hourly:
            console.print(
                f"[cyan]Fetching hourly forecast for {final_location}...[/cyan]"
            )
            items = client.get_hourly_forecast(final_location, hours=days * 24)

            table = Table(
                title=f"Hourly Forecast: {final_location}", box=box.SIMPLE_HEAD
            )
            table.add_column("Time", style="dim")
            table.add_column("Temp", style="bold cyan")
            table.add_column("Condition", style="white")
            table.add_column("Wind", style="green")
            table.add_column("Precip", style="blue")

            for item in items:
                time_str = format_dt(item.timestamp)
                unit_label = (
                    "°F"
                    if "FAHRENHEIT" in (item.temperature.units or "").upper()
                    else "°C"
                )
                temp_str = f"{item.temperature.value}{unit_label}"
                wind_str = f"{item.wind.speed} {item.wind.direction}"
                precip_str = f"{item.precipitation.probability}%"
                if item.precipitation.rate and item.precipitation.rate > 0:
                    precip_str += f' ({item.precipitation.rate}")'

                table.add_row(
                    time_str, temp_str, item.description, wind_str, precip_str
                )
            console.print(table)

        else:
            console.print(
                f"[cyan]Fetching daily forecast for {final_location} ({days} days)...[/cyan]"
            )
            items = client.get_daily_forecast(final_location, days=days)

            table = Table(
                title=f"Daily Forecast: {final_location}", box=box.SIMPLE_HEAD
            )
            table.add_column("Date", style="dim")
            table.add_column("High/Low", style="bold cyan")
            table.add_column("Condition", style="white")
            table.add_column("Precip", style="blue")
            table.add_column("Sun", style="yellow")

            for item in items:
                date_str = format_date(item.date)
                unit_label = (
                    "°F"
                    if "FAHRENHEIT" in (item.high_temp.units or "").upper()
                    else "°C"
                )
                temp_str = f"{item.high_temp.value}{unit_label} / {item.low_temp.value}{unit_label}"

                sun_str = ""
                if item.sunrise and item.sunset:
                    sun_str = f"☀ {format_dt(item.sunrise)} ↓ {format_dt(item.sunset)}"

                precip_val = f"{item.precipitation_probability}%"
                # Daily item doesn't have rate easily accessible in my model?
                # I mapped `precipitation_probability` but `precipitation` object has `qpf` too.
                # I need to update DailyForecastItem model to include rate/qpf.
                # For now, let's just stick to probability for Daily or check if I can grab rate.

                table.add_row(date_str, temp_str, item.description, precip_val, sun_str)
            console.print(table)

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def alert(location_arg, location):
    """
    Check for severe weather alerts.

    Displays active warnings, watches, and advisories.

    \b
    EXAMPLES:
      atmos alert
      atmos alert -L "Miami, FL"
    """
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
                border_style="red",
            )
            console.print(panel)

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option("--hours", default=24, help="Number of hours to graph (default: 24)")
@click.option(
    "--metric",
    default="temp",
    type=click.Choice(["temp", "precip", "wind"]),
    help="Metric to graph",
)
def graph(location_arg, location, hours, metric):
    """
    Visualize weather trends (ASCII Graph).

    Draws a chart directly in the terminal.

    \b
    EXAMPLES:
      atmos graph
      atmos graph --metric precip --hours 48
    """
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
            if metric == "temp":
                val = item.temperature.value or 0.0
            elif metric == "precip":
                val = item.precipitation.probability or 0.0
            elif metric == "wind":
                val = item.wind.speed or 0.0

            series.append(val)
            if i % 4 == 0:
                labels.append(format_dt(item.timestamp))
            else:
                labels.append("")

        console.print(f"\n[bold]{metric.title()} Trend ({hours}h)[/bold]")

        cfg = {"height": 15, "format": "{:8.1f}"}
        if metric == "temp":
            cfg["colors"] = [asciichartpy.red]
        elif metric == "precip":
            cfg["colors"] = [asciichartpy.blue]

        chart = asciichartpy.plot(series, cfg)
        console.print(Text.from_ansi(chart))

        start_t = format_dt(items[0].timestamp)
        end_t = format_dt(items[-1].timestamp)
        console.print(f"[dim]Time: {start_t} -> {end_t}[/dim]")

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
def stars(location_arg, location):
    """
    Astronomy info and stargazing forecast.

    Shows Sun/Moon rise/set times, phases, and a stargazing condition report.

    \b
    EXAMPLES:
      atmos stars
      atmos stars -L "Joshua Tree"
    """
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

        condition_report = get_stargazing_conditions(
            today.cloud_cover or 0, today.moon_phase or "Unknown"
        )

        # Calculate Daylight
        daylight_str = "-"
        if today.sunrise and today.sunset:
            diff = today.sunset - today.sunrise
            hours, remainder = divmod(diff.seconds, 3600)
            minutes = remainder // 60
            daylight_str = f"{hours}h {minutes}m"

        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column()
        grid.add_column()

        sun_table = Table.grid(padding=(0, 1))
        sun_table.add_column(style="bold yellow", width=12)
        sun_table.add_column()

        sun_table.add_row("☀ Sun", "")
        sun_table.add_row(
            "Rise:", format_time_ampm(today.sunrise) if today.sunrise else "-"
        )
        sun_table.add_row(
            "Set:", format_time_ampm(today.sunset) if today.sunset else "-"
        )
        sun_table.add_row("Daylight:", daylight_str)

        moon_table = Table.grid(padding=(0, 1))
        moon_table.add_column(style="bold white", width=12)
        moon_table.add_column()

        moon_table.add_row("☾ Moon", "")
        moon_table.add_row("Phase:", today.moon_phase.replace("_", " ").title())
        moon_table.add_row(
            "Rise:", format_time_ampm(today.moonrise) if today.moonrise else "-"
        )
        moon_table.add_row(
            "Set:", format_time_ampm(today.moonset) if today.moonset else "-"
        )

        grid.add_row(sun_table, moon_table)

        grid.add_row("", "")
        grid.add_row("", "")

        cond_table = Table.grid(padding=(0, 1))
        cond_table.add_column(style="bold blue", width=12)
        cond_table.add_column()

        cond_table.add_row("☁ Conditions", "")
        cond_table.add_row(
            "Cloud Cover:", f"{today.cloud_cover}% ({condition_report.split('.')[0]})"
        )
        cond_table.add_row("Precip:", f"{today.precipitation_probability}%")
        cond_table.add_row("Stargazing:", f"[italic]{condition_report}[/italic]")

        final_layout = Table.grid(expand=True)
        final_layout.add_row(grid)
        final_layout.add_row(cond_table)

        date_str = format_date(today.date)
        console.print(
            Panel(
                final_layout,
                title=f"Astronomy: {final_location} ({date_str})",
                border_style="magenta",
                expand=False,
            )
        )

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@main.command()
@click.argument("location_arg", required=False)
@click.option("-L", "--location", help="City or location name")
@click.option(
    "-a", "--activity", required=True, help="Activity (hiking, bbq, beach, stargazing)"
)
@click.option("-d", "--days", default=10, help="Search range (default: 10 days)")
def find(location_arg, location, activity, days):
    """
    Find the best day for an activity.

    Analyzes forecast conditions against activity rules.

    \b
    ACTIVITIES:
      hiking, bbq, beach, stargazing, running, cycling, golf,
      sailing, skiing, drone, photography, tennis, camping, fishing, kayaking

    \b
    EXAMPLES:
      atmos find --activity hiking
      atmos find -L "San Diego" --activity beach --days 5
    """
    target = location_arg or location
    if not target:
        console.print("[bold red]Error:[/bold red] Missing location.")
        return

    saved_address = places_manager.get(target)
    final_location = saved_address if saved_address else target

    try:
        console.print(
            f"[cyan]Searching best day for [bold]{activity}[/bold] in {final_location} (Next {days} days)...[/cyan]"
        )
        items = client.get_daily_forecast(final_location, days=days)

        scored_days = []
        for item in items:
            score, reasons = SuitabilityEvaluator.evaluate(item, activity)
            scored_days.append(
                {"date": item.date, "score": score, "reasons": reasons, "item": item}
            )

        # Sort by Score DESC
        scored_days.sort(key=lambda x: x["score"], reverse=True)

        # Display Top 3
        table = Table(title=f"Best Days for {activity.title()}", box=box.SIMPLE_HEAD)
        table.add_column("Rank", style="dim")
        table.add_column("Date", style="bold")
        table.add_column("Score", justify="center")
        table.add_column("Forecast")
        table.add_column("Notes", style="red")

        for i, d in enumerate(scored_days[:5]):
            score_color = (
                "green" if d["score"] >= 80 else "yellow" if d["score"] >= 50 else "red"
            )
            score_str = f"[{score_color}]{d['score']}/100[/{score_color}]"

            date_str = format_date(d["date"])

            # Forecast summary
            f = d["item"]
            high = f.high_temp.value
            cond = f.description
            summary = f"{high}°F, {cond}"

            notes = ", ".join(d["reasons"])

            table.add_row(str(i + 1), date_str, score_str, summary, notes)

        console.print(table)

    except AtmosAPIError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}")
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
