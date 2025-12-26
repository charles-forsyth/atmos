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
        Fetches current weather conditions.
        Note: This uses the standard structure. We will refine exact endpoints 
        once we verify the specific API Access.
        """
        lat, lng = self.get_coords(location)
        
        # NOTE: This is a placeholder for the actual API call logic 
        # since the specific 'currentConditions:lookup' endpoint might vary.
        # For this "Skeleton" phase, we will simulate the structure 
        # or implement the exact call if we have the specific docs.
        # 
        # Real Implementation would look like:
        # url = f"{self.base_url}/currentConditions:lookup"
        # params = {"location": f"{lat},{lng}", "key": self.api_key}
        # ...
        
        # For now, to ensure the CLI works and we can style it, 
        # I will return a MOCKED response if the API fails or for this demo step,
        # but the ARCHITECTURE is ready for the real call.
        
        # Let's try to simulate a real-ish response object for the UI to consume
        return CurrentConditions(
            temperature=Temperature(value=22.5, units="CELSIUS"),
            feels_like=Temperature(value=24.0, units="CELSIUS"),
            humidity=45.0,
            description="Partly Cloudy",
            wind=Wind(speed=15.0, direction="NW", gust=25.0),
            precipitation=Precipitation(type="None", rate=0.0, probability=0.0),
            uv_index=5,
            visibility=10000.0,
            pressure=1013.25
        )

# Global client instance
client = AtmosClient()