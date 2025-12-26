from typing import List, Tuple
from atmos.models import DailyForecastItem

class SuitabilityEvaluator:
    """Evaluates weather conditions for specific activities."""
    
    ACTIVITIES = {
        "hiking": ["hiking", "hike", "walk", "trek"],
        "bbq": ["bbq", "barbecue", "grill", "picnic"],
        "stargazing": ["stargazing", "stars", "astronomy"],
        "beach": ["beach", "swim", "ocean"],
        "running": ["running", "jogging", "run"],
        "cycling": ["cycling", "bike", "biking"],
        "golf": ["golf", "golfing"],
        "sailing": ["sailing", "boating"],
        "skiing": ["skiing", "snowboarding", "ski"],
        "drone": ["drone", "flying"],
        "photography": ["photography", "photo"],
        "tennis": ["tennis"],
        "camping": ["camping", "camp"],
        "fishing": ["fishing", "fish"]
    }

    @staticmethod
    def evaluate(day: DailyForecastItem, activity: str) -> Tuple[int, List[str]]:
        """Returns score (0-100) and list of reasons/warnings."""
        score = 100
        reasons = []
        
        act = activity.lower()
        # Resolve alias
        resolved = False
        for key, aliases in SuitabilityEvaluator.ACTIVITIES.items():
            if act == key or act in aliases:
                act = key
                resolved = True
                break
        
        # If unknown activity, generic logic
        if not resolved:
            reasons.append("Unknown activity (Using generic logic)")
        
        precip = day.precipitation_probability or 0.0
        
        high = day.high_temp.value or 0.0
        low = day.low_temp.value or 0.0
        if day.high_temp.units == "CELSIUS":
            high = (high * 9/5) + 32
            low = (low * 9/5) + 32
            
        wind = 0.0
        if day.max_wind:
            wind = day.max_wind.speed or 0.0
        
        cloud = day.cloud_cover or 0

        # --- Base Rules ---
        
        # Rain is generally bad
        if precip > 70:
            score -= 80
            reasons.append(f"High rain chance ({precip}%)")
        elif precip > 30:
            score -= 30
            reasons.append(f"Chance of rain ({precip}%)")
            
        # --- Specific Rules ---
        
        if act == "hiking":
            if high > 90:
                score -= 30
                reasons.append(f"Hot ({high}°F)")
            if high < 30:
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
                score -= 30 
            if wind > 15:
                score -= 20
                reasons.append("Windy")
                
        elif act == "stargazing":
            score = 100 # Reset
            if cloud > 50:
                score -= 80
                reasons.append(f"Cloudy ({cloud}%)")
            elif cloud > 20:
                score -= 30
                reasons.append(f"Some clouds ({cloud}%)")
            
            # Penalize Full Moon
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
            if wind > 15:
                score -= 10
                reasons.append("Breezy")

        elif act == "running":
            if high > 80:
                score -= 40
                reasons.append(f"Too hot ({high}°F)")
            elif high > 70:
                score -= 10
                reasons.append("Warm")
            elif high < 32:
                score -= 20
                reasons.append("Freezing")
            
            # Runners hate rain but tolerate drizzle
            if precip > 60:
                score -= 20 # Already penalized by base rule, add more?
            
        elif act == "cycling":
            if wind > 20:
                score -= 60
                reasons.append(f"High Wind ({wind} mph)")
            elif wind > 12:
                score -= 20
                reasons.append(f"Breezy ({wind} mph)")
            
            if precip > 20:
                score -= 40 # Slippery
                reasons.append("Wet roads")

        elif act == "golf":
            if wind > 15:
                score -= 40
                reasons.append("Wind affects ball")
            if precip > 20:
                score -= 50
                reasons.append("Rain")
            if high < 50:
                score -= 20
                reasons.append("Chilly")

        elif act == "sailing":
            score = 100 # Reset base
            if wind < 5:
                score -= 50
                reasons.append("No wind (Calm)")
            elif wind > 20:
                score -= 60
                reasons.append(f"Dangerous Wind ({wind} mph)")
            
            if precip > 50:
                score -= 30
            
            if high < 50:
                score -= 20
                reasons.append("Cold on water")

        elif act == "skiing":
            score = 100
            if high > 40:
                score -= 80
                reasons.append(f"Too warm ({high}°F)")
            elif high > 32:
                score -= 40
                reasons.append("Mushy/Melting")
            
            # Snow is good!
            # We don't have precipitation TYPE easily accessible in daily sum yet
            # But if precip prob is high and temp is low, it's likely snow.
            if precip > 50 and high < 32:
                score += 10 # Bonus
                reasons.append("Fresh Powder likely")

        elif act == "drone":
            if wind > 15:
                score -= 100
                reasons.append("Wind unsafe")
            if precip > 10:
                score -= 100
                reasons.append("Rain risk")
            if cloud > 90:
                score -= 20 # Visibility
            if high < 32:
                score -= 20 # Battery efficiency

        elif act == "photography":
            # Photographers like Golden Hour / Blue Hour (Sunrise/Sunset)
            # They dislike flat grey sky (100% cloud) or empty blue sky (0% cloud) sometimes?
            # Let's say overcast is bad.
            if cloud > 90:
                score -= 40
                reasons.append("Flat light")
            elif cloud == 0:
                score -= 10
                reasons.append("Harsh light")
            
            if precip > 30:
                score -= 50
                reasons.append("Rain")

        elif act == "tennis":
            if wind > 12:
                score -= 40
                reasons.append("Windy")
            if precip > 10:
                score -= 80 # Wet court
                reasons.append("Wet court")

        elif act == "camping":
            if low < 40:
                score -= 40
                reasons.append(f"Cold night ({low}°F)")
            if precip > 30:
                score -= 60
                reasons.append("Rain")

        elif act == "fishing":
            if wind > 15:
                score -= 40
                reasons.append("Choppy water")
            # Barometric pressure trends are best but daily data is limited
            if precip > 60:
                score -= 30
                reasons.append("Heavy rain")

        # Cap score
        score = max(0, min(100, score))
        return score, reasons
