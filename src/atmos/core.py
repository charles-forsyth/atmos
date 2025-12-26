import requests
from typing import Tuple, List, Dict, Any
from datetime import datetime
from atmos.config import settings
from atmos.models import (
    CurrentConditions, Temperature, Wind, Precipitation, 
    HourlyHistoryItem, HourlyForecastItem, DailyForecastItem
)
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
        vis_val = vis_obj.get("distance", 10.0)
        
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
        
        url = f"{self.base_url}/history/hours:lookup"
        
        fetch_hours = min(hours, 24)
        
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "hours": fetch_hours, 
            "key": self.api_key,
            "unitsSystem": "IMPERIAL",
            "pageSize": fetch_hours
        }
        
        resp = requests.get(url, params=params)
        
        if not resp.ok:
            raise ValueError(f"History API Error ({resp.status_code}): {resp.text}")
            
        data = resp.json()
        
        history_items = []
        entries = data.get("historyHours", [])
        
        for entry in entries:
            interval = entry.get("interval", {})
            ts_str = interval.get("startTime")
            
            if not ts_str:
                continue
            
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
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

    def get_hourly_forecast(self, location: str, hours: int = 24) -> List[HourlyForecastItem]:
        """Fetches hourly forecast."""
        lat, lng = self.get_coords(location)
        url = f"{self.base_url}/forecast/hours:lookup"
        
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "hours": min(hours, 240), # API limit 240
            "key": self.api_key,
            "unitsSystem": "IMPERIAL",
            "pageSize": min(hours, 24) 
        }
        
        resp = requests.get(url, params=params)
        if not resp.ok:
            raise ValueError(f"Forecast API Error ({resp.status_code}): {resp.text}")
            
        data = resp.json()
        entries = data.get("forecastHours", []) # Guessing key
        
        items = []
        for entry in entries:
            interval = entry.get("interval", {})
            ts_str = interval.get("startTime")
            if not ts_str:
                continue
            
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            temp, feels_like, wind, precip, desc, humidity, pressure = self._parse_condition(entry)
            
            items.append(HourlyForecastItem(
                timestamp=ts, temperature=temp, feels_like=feels_like,
                humidity=humidity, description=desc, wind=wind,
                precipitation=precip, pressure=pressure
            ))
        return items

    def get_daily_forecast(self, location: str, days: int = 5) -> List[DailyForecastItem]:
        """Fetches daily forecast."""
        lat, lng = self.get_coords(location)
        url = f"{self.base_url}/forecast/days:lookup"
        
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "days": min(days, 10),
            "key": self.api_key,
            "unitsSystem": "IMPERIAL"
        }
        
        resp = requests.get(url, params=params)
        if not resp.ok:
            raise ValueError(f"Daily Forecast API Error ({resp.status_code}): {resp.text}")
            
        data = resp.json()
        entries = data.get("forecastDays", [])
        
        items = []
        for entry in entries:
            # Parse Date from interval? or 'displayDateTime'?
            interval = entry.get("interval", {})
            ts_str = interval.get("startTime")
            if not ts_str:
                continue
            
            date = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            
            # Temps are likely highTemperature / lowTemperature objects
            low_obj = entry.get("lowTemperature", {})
            high_obj = entry.get("highTemperature", {})
            
            low_temp = Temperature(value=low_obj.get("degrees", 0.0), units=low_obj.get("unit", "CELSIUS"))
            high_temp = Temperature(value=high_obj.get("degrees", 0.0), units=high_obj.get("unit", "CELSIUS"))
            
            cond_obj = entry.get("weatherCondition", {})
            desc_obj = cond_obj.get("description", {})
            desc = desc_obj.get("text", cond_obj.get("type", "Unknown"))
            
            precip_obj = entry.get("precipitation", {})
            prob = precip_obj.get("maxProbability", {}).get("percent", 0.0) # Daily usually has maxProb
            
            # Sunrise/Sunset
            sun_obj = entry.get("sunEvents", {})
            sunrise_str = sun_obj.get("sunriseTime")
            sunset_str = sun_obj.get("sunsetTime")
            
            sunrise = datetime.fromisoformat(sunrise_str.replace("Z", "+00:00")) if sunrise_str else None
            sunset = datetime.fromisoformat(sunset_str.replace("Z", "+00:00")) if sunset_str else None
            
            items.append(DailyForecastItem(
                date=date,
                low_temp=low_temp,
                high_temp=high_temp,
                description=desc,
                precipitation_probability=prob,
                sunrise=sunrise,
                sunset=sunset
            ))
            
        return items

# Global client instance
client = AtmosClient()
