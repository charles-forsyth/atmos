from datetime import datetime


def format_temp(temp: float) -> str:
    return f"{temp}°C"


def get_stargazing_conditions(cloud_cover_percent: float, moon_phase: str) -> str:
    """Returns a stargazing quality rating and prominent constellations."""

    # 1. Rating Logic
    rating = "Poor"
    if cloud_cover_percent < 20:
        rating = "Excellent"
    elif cloud_cover_percent < 50:
        rating = "Good"
    elif cloud_cover_percent < 80:
        rating = "Fair"

    # Moon impact
    moon_impact = ""
    if "FULL" in moon_phase.upper() or "GIBBOUS" in moon_phase.upper():
        moon_impact = " (Bright Moon)"
        if rating == "Excellent":
            rating = "Good"  # Downgrade due to light pollution

    # 2. Seasonality (Northern Hemisphere Default)
    # Simple static lookup based on current month
    month = datetime.now().month
    constellations = []

    if month in [12, 1, 2]:  # Winter
        constellations = ["Orion", "Taurus", "Gemini", "Canis Major"]
    elif month in [3, 4, 5]:  # Spring
        constellations = ["Leo", "Virgo", "Ursa Major (Big Dipper)"]
    elif month in [6, 7, 8]:  # Summer
        constellations = ["Scorpius", "Cygnus", "Lyra", "Aquila"]
    else:  # Fall
        constellations = ["Pegasus", "Andromeda", "Cassiopeia"]

    return f"{rating}{moon_impact}. Look for: {', '.join(constellations)}."
