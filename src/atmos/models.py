from pydantic import BaseModel
from typing import Optional

# --- Weather Data Models ---

class Temperature(BaseModel):
    value: float = 0.0
    units: str = "CELSIUS"

class Wind(BaseModel):
    speed: Optional[float] = 0.0
    direction: Optional[str] = "N"
    gust: Optional[float] = 0.0

class Precipitation(BaseModel):
    type: str = "None"
    rate: float = 0.0
    probability: float = 0.0

class CurrentConditions(BaseModel):
    temperature: Temperature
    feels_like: Temperature
    humidity: float = 0.0
    description: str = "Unknown"
    wind: Wind
    precipitation: Precipitation
    uv_index: int = 0
    visibility: float = 10000.0
    pressure: float = 1013.25