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
        "fishing": ["fishing", "fish"],
        "kayaking": ["kayaking", "kayak", "canoe", "paddling"]
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
        if precip > 70:
            score -= 80
            reasons.append(f"High rain chance ({precip}%)")
        elif precip > 30:
            score -= 30
            reasons.append(f"Chance of rain ({precip}%)")
        elif precip < 10:
            pass
            
        # --- Specific Rules ---
        
        if act == "hiking":
            if high > 90:
                score -= 30
                reasons.append(f"Hot ({high}°F)")
            elif high > 60 and high < 80:
                reasons.append("Great temp")
                
            if high < 30:
                score -= 20
                reasons.append(f"Cold ({high}°F)")
                
            if wind > 20:
                score -= 30
                reasons.append(f"Windy ({wind} mph)")
                
        elif act == "bbq":
            if high < 60:
                score -= 30
                reasons.append(f"Chilly ({high}°F)")
            elif high > 70:
                reasons.append("Warm")
                
            if precip > 20: 
                score -= 30
                reasons.append("Rain risk")
            
            if wind > 15:
                score -= 20
                reasons.append("Breezy")
                
        elif act == "stargazing":
            score = 100 
            if cloud > 50:
                score -= 80
                reasons.append(f"Cloudy ({cloud}%)")
            elif cloud > 20:
                score -= 30
                reasons.append(f"Some clouds ({cloud}%)")
            elif cloud < 10:
                reasons.append("Clear skies")
            
            phase = (day.moon_phase or "").upper()
            if "FULL" in phase or "GIBBOUS" in phase:
                score -= 40
                reasons.append(f"Bright Moon ({day.moon_phase})")
            elif "NEW" in phase or "CRESCENT" in phase:
                reasons.append("Dark sky")
                
        elif act == "beach":
            if high < 75:
                score -= 50
                reasons.append(f"Too cold ({high}°F)")
            elif high > 85:
                reasons.append("Hot & Sunny")
                
            if cloud > 60:
                score -= 20
                reasons.append("No sun")
            elif cloud < 20:
                reasons.append("Sunny")
                
            if wind > 15:
                score -= 10
                reasons.append("Breezy")

        elif act == "running":
            if high > 80:
                score -= 40
                reasons.append(f"Heat ({high}°F)")
            elif high > 70:
                score -= 10
                reasons.append("Warm")
            elif high >= 45 and high <= 65:
                reasons.append("Perfect running temp")
            elif high < 32:
                score -= 20
                reasons.append("Freezing")
            
            if precip > 60:
                score -= 20
            
        elif act == "cycling":
            if wind > 20:
                score -= 60
                reasons.append(f"High Wind ({wind} mph)")
            elif wind > 12:
                score -= 20
                reasons.append(f"Headwind ({wind} mph)")
            else:
                reasons.append("Low wind")
            
            if precip > 20:
                score -= 40
                reasons.append("Slippery")

        elif act == "golf":
            if wind > 15:
                score -= 40
                reasons.append("Windy")
            if precip > 20:
                score -= 50
                reasons.append("Rain")
            if high < 50:
                score -= 20
                reasons.append("Chilly")
            elif high >= 65 and high <= 85:
                reasons.append("Ideal temp")

        elif act == "sailing":
            score = 100 
            if wind < 5:
                score -= 50
                reasons.append("No wind (Calm)")
            elif wind >= 10 and wind <= 20:
                reasons.append("Perfect wind")
            elif wind > 20:
                score -= 60
                reasons.append(f"Dangerous Wind ({wind} mph)")
            
            if precip > 50:
                score -= 30
            
            if high < 50:
                score -= 20
                reasons.append("Cold spray")

        elif act == "skiing":
            score = 100
            if high > 40:
                score -= 80
                reasons.append(f"Slushy ({high}°F)")
            elif high > 32:
                score -= 40
                reasons.append("Melting")
            elif high < 10:
                reasons.append("Frigid")
            else:
                reasons.append("Good snow temp")
            
            if precip > 50 and high < 32:
                score += 10
                reasons.append("Fresh Powder likely")

        elif act == "drone":
            if wind > 15:
                score -= 100
                reasons.append("Wind unsafe")
            else:
                reasons.append("Stable air")
                
            if precip > 10:
                score -= 100
                reasons.append("Rain risk")
            if cloud > 90:
                score -= 20
            if high < 32:
                score -= 20 

        elif act == "photography":
            if cloud > 90:
                score -= 40
                reasons.append("Flat light")
            elif cloud == 0:
                score -= 10
                reasons.append("Harsh light")
            elif cloud >= 20 and cloud <= 70:
                reasons.append("Dramatic sky")
            
            if precip > 30:
                score -= 50
                reasons.append("Rain")

        elif act == "tennis":
            if wind > 12:
                score -= 40
                reasons.append("Windy")
            if precip > 10:
                score -= 80 
                reasons.append("Wet court")
            elif high >= 60 and high <= 80:
                reasons.append("Great weather")

        elif act == "camping":
            if low < 40:
                score -= 40
                reasons.append(f"Cold night ({low}°F)")
            elif low > 50:
                reasons.append("Mild night")
                
            if precip > 30:
                score -= 60
                reasons.append("Rain")

        elif act == "fishing":
            if wind > 15:
                score -= 40
                reasons.append("Choppy water")
            else:
                reasons.append("Calm water")
            if precip > 60:
                score -= 30
                reasons.append("Heavy rain")

        elif act == "kayaking":
            score = 100
            if wind > 20:
                score -= 80
                reasons.append(f"Dangerous water ({wind} mph)")
            elif wind > 10:
                score -= 30
                reasons.append(f"Choppy ({wind} mph)")
            else:
                reasons.append("Calm water")
                
            if high < 50:
                score -= 40
                reasons.append(f"Cold water risk ({high}°F)")
            elif high > 70:
                reasons.append("Warm air")
                
            if precip > 40:
                score -= 30
                reasons.append("Rain")

        # Cap score
        score = max(0, min(100, score))
        
        # If perfect score and no reasons, add a generic good one
        if score == 100 and not reasons:
            reasons.append("Excellent conditions")
            
        return score, reasons
