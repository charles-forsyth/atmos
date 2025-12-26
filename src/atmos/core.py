import requests
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta, timezone
from atmos.config import settings
from atmos.models import CurrentConditions, Temperature, Wind, Precipitation, HourlyHistoryItem
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

    def _parse_condition(self, data: Dict[str, Any]) -> Tuple[Temperature, Temperature, Wind, Precipitation, str, float, float]:
        """Helper to parse common fields from a data block (current or history)."""
        # Temperature
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

        # Wind
        wind_obj = data.get("wind", {})
        speed_obj = wind_obj.get("speed", {})
        gust_obj = wind_obj.get("gust", {})
        direction_obj = wind_obj.get("direction", {})
        
        wind = Wind(
            speed=speed_obj.get("value", 0.0),
            direction=direction_obj.get("cardinal", "N"),
            gust=gust_obj.get("value", 0.0)
        )

        # Precipitation
        precip_obj = data.get("precipitation", {})
        prob_obj = precip_obj.get("probability", {})
        qpf_obj = precip_obj.get("qpf", {})
        
        precip = Precipitation(
            type=prob_obj.get("type", "None"),
            rate=qpf_obj.get("quantity", 0.0),
            probability=prob_obj.get("percent", 0.0)
        )
        
        # Description
        cond_obj = data.get("weatherCondition", {})
        desc_obj = cond_obj.get("description", {})
        description = desc_obj.get("text", cond_obj.get("type", "Unknown"))
        
        # Pressure
        pressure_obj = data.get("airPressure", {})
        pressure = pressure_obj.get("meanSeaLevelMillibars", 1013.25)

        # Humidity
        humidity = data.get("relativeHumidity", 0.0)

        return temp, feels_like, wind, precip, description, humidity, pressure


    def get_current_conditions(self, location: str) -> CurrentConditions:
        """Fetches real current weather conditions."""
        lat, lng = self.get_coords(location)
        
        url = f"{self.base_url}/currentConditions:lookup"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "key": self.api_key,
            "unitsSystem": "IMPERIAL"
        }
        
        resp = requests.get(url, params=params)
        
        if not resp.ok:
            raise ValueError(f"Weather API Error ({resp.status_code}): {resp.text}")

        data = resp.json()
        cond = data.get("currentConditions", data)
        
        temp, feels_like, wind, precip, desc, humidity, pressure = self._parse_condition(cond)
        
        # Visibility
        vis_obj = cond.get("visibility", {})
        # Use raw val, let UI handle unit display if needed.
        vis_val = vis_obj.get("distance", 10.0)
        # Note: if units are KILOMETERS, we might want to normalize? 
        # For now, passing raw.
        
        return CurrentConditions(
            temperature=temp,
            feels_like=feels_like,
            humidity=humidity,
            description=desc,
            wind=wind,
            precipitation=precip,
            uv_index=cond.get("uvIndex", 0),
            visibility=vis_val,
            pressure=pressure
        )

    def get_hourly_history(self, location: str, hours: int = 24) -> List[HourlyHistoryItem]:
        """Fetches hourly history for the last N hours."""
        lat, lng = self.get_coords(location)
        
        # Time calculation (UTC)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Format timestamps RFC3339
        # 2023-10-05T12:00:00Z
        
        url = f"{self.base_url}/history:lookup"
        
        # Note: 'history:lookup' might be 'historyVersions/2/history:lookup' or similar.
        # We try the standard pattern first.
        
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "key": self.api_key,
            "unitsSystem": "IMPERIAL",
            "pageSize": 24 # or 'hours'
        }
        
        resp = requests.get(url, params=params)
        
        if not resp.ok:
            raise ValueError(f"History API Error ({resp.status_code}): {resp.text}")
            
        data = resp.json()
        # console.print(data) # Debug if needed
        
        history_items = []
        # API returns 'historyEntries' usually
        entries = data.get("historyEntries", [])
        
        for entry in entries:
            # Entry has 'startTime' (the hour) and condition data
            # Condition data is usually nested or flat? 
            # Often 'condition' key.
            # Let's check structure via trial/error (or debug print if fails)
            
            # Assuming: entry = { "startTime": "...", "condition": { ... } }
            # Or entry IS the condition with a time field.
            
            ts_str = entry.get("startTime") or entry.get("endTime") # timestamp
            if not ts_str:
                continue
            
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            
            # The condition data is likely mixed in or in a sub-object
            # Docs say 'historyEntries[]' -> each has fields.
            
            temp, feels_like, wind, precip, desc, humidity, pressure = self._parse_condition(entry)
            
            item = HourlyHistoryItem(
                timestamp=ts,
                temperature=temp,
                feels_like=feels_like,
                humidity=humidity,
                description=desc,
                wind=wind,
                precipitation=precip,
                pressure=pressure
            )
            history_items.append(item)
            
        return history_items

# Global client instance
client = AtmosClient()