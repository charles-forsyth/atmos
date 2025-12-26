from pydantic import BaseModel
from typing import Optional

# --- Weather Data Models ---

class Temperature(BaseModel):
    value: float
    units: str = "CELSIUS"

class Wind(BaseModel):
    speed: Optional[float] = None
    direction: Optional[str] = None # e.g., "NE" or degrees
    gust: Optional[float] = None

class Precipitation(BaseModel):
    type: str = "None"
    rate: float = 0.0 # mm/hr
    probability: float = 0.0

class CurrentConditions(BaseModel):
    temperature: Temperature
    feels_like: Temperature
    humidity: float # Percentage
    description: str # "Sunny", "Partly Cloudy"
    wind: Wind
    precipitation: Precipitation
    uv_index: int
    visibility: float # meters
    pressure: float # hPa
    
    # We can add more fields as we discover the exact API response structure
