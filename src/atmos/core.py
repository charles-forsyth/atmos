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
        
        # The API returns a direct object structure (based on debug output)
        # We parse carefully.
        
        # 1. Temperature
        temp_obj = data.get("temperature", {})
        temp = Temperature(
            value=temp_obj.get("degrees", 0.0),
            units=temp_obj.get("unit", "CELSIUS")
        )
        
        feels_like_obj = data.get("feelsLikeTemperature", {})
        feels_like = Temperature(
            value=feels_like_obj.get("degrees", 0.0),
            units=feels_like_obj.get("unit", "CELSIUS")
        )

        # 2. Wind
        wind_obj = data.get("wind", {})
        speed_obj = wind_obj.get("speed", {})
        gust_obj = wind_obj.get("gust", {})
        direction_obj = wind_obj.get("direction", {})
        
        wind = Wind(
            speed=speed_obj.get("value", 0.0),
            direction=direction_obj.get("cardinal", "N"),
            gust=gust_obj.get("value", 0.0)
        )

        # 3. Precipitation
        precip_obj = data.get("precipitation", {})
        prob_obj = precip_obj.get("probability", {})
        # Rate might be inside 'qpf' or 'snowQpf'
        # For now, let's look for qpf.quantity
        qpf_obj = precip_obj.get("qpf", {})
        
        precip = Precipitation(
            type=prob_obj.get("type", "None"),
            rate=qpf_obj.get("quantity", 0.0),
            probability=prob_obj.get("percent", 0.0)
        )
        
        # 4. Others
        # conditionDescription is inside weatherCondition.description.text (or type)
        cond_obj = data.get("weatherCondition", {})
        desc_obj = cond_obj.get("description", {})
        description = desc_obj.get("text", cond_obj.get("type", "Unknown"))
        
        # Pressure
        pressure_obj = data.get("airPressure", {})

        # Visibility
        vis_obj = data.get("visibility", {})

        return CurrentConditions(
            temperature=temp,
            feels_like=feels_like,
            humidity=data.get("relativeHumidity", 0.0),
            description=description,
            wind=wind,
            precipitation=precip,
            uv_index=data.get("uvIndex", 0),
            visibility=vis_obj.get("distance", 10.0) * 1000 if vis_obj.get("unit") == "KILOMETERS" else vis_obj.get("distance", 10000.0),
            pressure=pressure_obj.get("meanSeaLevelMillibars", 1013.25)
        )

# Global client instance
client = AtmosClient()