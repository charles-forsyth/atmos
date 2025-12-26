import requests
from typing import Tuple
from atmos.config import settings
from atmos.models import CurrentConditions, Temperature, Wind, Precipitation

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
        resp.raise_for_status()
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
            "location": f"{lat},{lng}",
            "key": self.api_key,
            "units": "METRIC" # Request Metric by default, logic handles display
        }
        
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        # The API returns a 'currentConditions' object inside the response usually,
        # or sometimes direct fields depending on the version. 
        # We assume the standard structure:
        # { "currentConditions": { "temperature": { "value": 20, "units": "CELSIUS" }, ... } }
        
        # If the structure is flat, we adjust. Based on docs, it's usually currentConditions key.
        cond = data.get("currentConditions", data)
        
        # Parse Temperature
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

        # Parse Wind
        wind_data = cond.get("wind", {})
        wind = Wind(
            speed=wind_data.get("speed", 0.0),
            direction=wind_data.get("direction", "N"), # degrees or cardinal? API usually gives degrees or string
            gust=wind_data.get("gust", 0.0)
        )

        # Parse Precipitation
        precip_data = cond.get("precipitation", {})
        precip = Precipitation(
            type=precip_data.get("type", "None"),
            rate=precip_data.get("rate", 0.0),
            probability=precip_data.get("probability", 0.0)
        )

        return CurrentConditions(
            temperature=temp,
            feels_like=feels_like,
            humidity=cond.get("humidity", 0.0),
            description=cond.get("conditionDescription", "Unknown"), # e.g. "Sunny"
            wind=wind,
            precipitation=precip,
            uv_index=cond.get("uvIndex", 0),
            visibility=cond.get("visibility", 10000.0), # meters
            pressure=cond.get("pressure", 1013.25) # hPa
        )

# Global client instance
client = AtmosClient()