from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Weather Data Models ---

class Temperature(BaseModel):
    value: Optional[float] = 0.0
    units: Optional[str] = "CELSIUS"

class Wind(BaseModel):
    speed: Optional[float] = 0.0
    direction: Optional[str] = "N"
    gust: Optional[float] = 0.0

class Precipitation(BaseModel):
    type: Optional[str] = "None"
    rate: Optional[float] = 0.0
    probability: Optional[float] = 0.0

class CurrentConditions(BaseModel):
    temperature: Temperature
    feels_like: Temperature
    humidity: Optional[float] = 0.0
    description: Optional[str] = "Unknown"
    wind: Wind
    precipitation: Precipitation
    uv_index: Optional[int] = 0
    visibility: Optional[float] = 10000.0
    pressure: Optional[float] = 1013.25

class HourlyHistoryItem(BaseModel):
    timestamp: datetime
    temperature: Temperature
    feels_like: Temperature
    humidity: Optional[float] = 0.0
    description: Optional[str] = "Unknown"
    wind: Wind
    precipitation: Precipitation
    pressure: Optional[float] = 0.0

HourlyForecastItem = HourlyHistoryItem

class DailyForecastItem(BaseModel):
    date: datetime
    low_temp: Temperature
    high_temp: Temperature
    description: Optional[str] = "Unknown"
    precipitation_probability: Optional[float] = 0.0
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    moon_phase: Optional[str] = "Unknown"
    moonrise: Optional[datetime] = None
    moonset: Optional[datetime] = None
    cloud_cover: Optional[int] = 0 # Percentage

class WeatherAlert(BaseModel):
    headline: str
    description: str
    type: str 
    severity: str
    urgency: str
    certainty: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source: str