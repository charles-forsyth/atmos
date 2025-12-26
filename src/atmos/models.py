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
    """Represents a single hour of historical weather data."""
    timestamp: datetime
    temperature: Temperature
    feels_like: Temperature
    humidity: Optional[float] = 0.0
    description: Optional[str] = "Unknown"
    wind: Wind
    precipitation: Precipitation
    pressure: Optional[float] = 0.0