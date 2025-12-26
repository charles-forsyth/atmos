import requests
from typing import Tuple
from atmos.config import settings
from atmos.models import CurrentConditions, Temperature, Wind, Precipitation
from rich.console import Console

console = Console()

class AtmosClient:
    """
    Client for the Google Maps Platform Weather API.
    """
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is not set. Please check your configuration.")
            
        self.base_url = "https://weather.googleapis.com/v1" 
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def get_coords(self, location: str) -> Tuple[float, float]:
        """Resolves a string location to (lat, lng)."""
        params = {"address": location, "key": self.api_key}
        resp = requests.get(self.geocode_url, params=params)
        
        if not resp.ok:
            raise ValueError(f"Geocoding Error ({resp.status_code}): {resp.text}")
            
        data = resp.json()
        
        if not data.get("results"):
            raise ValueError(f"Location not found: {location}")
            
        loc = data["results"][0]["geometry"]["location"]
        return loc["lat"], loc["lng"]

    def get_current_conditions(self, location: str) -> CurrentConditions:
        """
        Fetches real current weather conditions from Google Maps Weather API.
        """
        lat, lng = self.get_coords(location)
        
        url = f"{self.base_url}/currentConditions:lookup"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "key": self.api_key,
            "unitsSystem": "METRIC"
        }
        
        resp = requests.get(url, params=params)
        
        if not resp.ok:
            raise ValueError(f"Weather API Error ({resp.status_code}): {resp.text}")

        data = resp.json()
        
        # DEBUG: Print raw response to understand the structure
        console.print("[yellow]DEBUG: Raw API Response:[/yellow]")
        console.print(data) 
        
        cond = data.get("currentConditions", data)
        
        temp_data = cond.get("temperature", {})
        temp = Temperature(
            value=temp_data.get("value", 0.0),
            units=temp_data.get("units", "CELSIUS")
        )
        
        feels_like_data = cond.get("feelsLikeTemperature", {})
        feels_like = Temperature(
            value=feels_like_data.get("value", 0.0),
            units=feels_like_data.get("units", "CELSIUS")
        )

        # Robust Wind Parsing
        wind_data = cond.get("wind", {})
        if wind_data is None:
            wind_data = {}
            
        wind = Wind(
            speed=wind_data.get("speed", 0.0),
            direction=wind_data.get("direction", "N"),
            gust=wind_data.get("gust", 0.0)
        )

        precip_data = cond.get("precipitation", {})
        if precip_data is None:
            precip_data = {}

        precip = Precipitation(
            type=precip_data.get("type", "None"),
            rate=precip_data.get("rate", 0.0),
            probability=precip_data.get("probability", 0.0)
        )

        return CurrentConditions(
            temperature=temp,
            feels_like=feels_like,
            humidity=cond.get("humidity", 0.0),
            description=cond.get("conditionDescription", "Unknown"),
            wind=wind,
            precipitation=precip,
            uv_index=cond.get("uvIndex", 0),
            visibility=cond.get("visibility", 10000.0),
            pressure=cond.get("pressure", 1013.25)
        )

# Global client instance
client = AtmosClient()
