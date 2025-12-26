from typing import List, Tuple
from atmos.models import DailyForecastItem

class SuitabilityEvaluator:
    """Evaluates weather conditions for specific activities."""
    
    ACTIVITIES = {
        "hiking": ["hiking", "hike", "walk", "trek"],
        "bbq": ["bbq", "barbecue", "grill", "picnic"],
        "stargazing": ["stargazing", "stars", "astronomy"],
        "beach": ["beach", "swim", "ocean"],
        "running": ["running", "jogging", "run"]
    }

    @staticmethod
    def evaluate(day: DailyForecastItem, activity: str) -> Tuple[int, List[str]]:
        """Returns score (0-100) and list of reasons/warnings."""
        score = 100
        reasons = []
        
        act = activity.lower()
        # Resolve alias
        for key, aliases in SuitabilityEvaluator.ACTIVITIES.items():
            if act in aliases:
                act = key
                break
        
        precip = day.precipitation_probability or 0.0
        
        high = day.high_temp.value or 0.0
        if day.high_temp.units == "CELSIUS":
            high = (high * 9/5) + 32
            
        # Use max_wind if available
        wind = 0.0
        if day.max_wind:
            wind = day.max_wind.speed or 0.0
        
        cloud = day.cloud_cover or 0

        # --- Logic Rules ---
        
        # Rule 1: Rain is bad for almost everything
        if precip > 70:
            score -= 80
            reasons.append(f"High rain chance ({precip}%)")
        elif precip > 30:
            score -= 40
            reasons.append(f"Chance of rain ({precip}%)")
            
        # Specifics
        if act == "hiking":
            if high > 90:
                score -= 30
                reasons.append(f"Hot ({high}°F)")
            if high < 40:
                score -= 20
                reasons.append(f"Cold ({high}°F)")
            if wind > 20:
                score -= 30
                reasons.append(f"Windy ({wind} mph)")
                
        elif act == "bbq":
            if high < 60:
                score -= 30
                reasons.append("Too cold")
            if precip > 20: 
                score -= 20 
            if wind > 15:
                score -= 20
                reasons.append("Windy")
                
        elif act == "stargazing":
            score = 100 
            if cloud > 50:
                score -= 80
                reasons.append(f"Cloudy ({cloud}%)")
            elif cloud > 20:
                score -= 30
                reasons.append(f"Some clouds ({cloud}%)")
                
            phase = (day.moon_phase or "").upper()
            if "FULL" in phase or "GIBBOUS" in phase:
                score -= 40
                reasons.append(f"Bright Moon ({day.moon_phase})")
                
        elif act == "beach":
            if high < 75:
                score -= 50
                reasons.append("Too cold")
            if cloud > 60:
                score -= 20
                reasons.append("No sun")

        # Cap score
        score = max(0, min(100, score))
        return score, reasons