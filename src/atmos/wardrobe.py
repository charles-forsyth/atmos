from typing import Any, Dict


class WardrobeAdviser:
    """Generates wardrobe and gear recommendations based on weather conditions."""

    @staticmethod
    def advise(
        temp_f: float,
        feels_like_f: float,
        precip_prob: float,
        precip_rate: float,
        uv_index: int,
        wind_speed: float,
        humidity: float,
        desc: str,
    ) -> Dict[str, Any]:
        clothing = []
        outerwear = []
        footwear = []
        gear = []
        warnings = []
        comfort_notes = []

        desc_lower = desc.lower()

        # 1. Temperature-based clothing layers
        if temp_f < 32:
            clothing.append("Heavy thermal base layers (wool or synthetic)")
            clothing.append("Warm fleece, flannel, or thick sweater")
            clothing.append("Thick insulated pants or lined trousers")
            outerwear.append("Heavy insulated winter parka (windproof & waterproof)")
            outerwear.append("Warm winter beanie/hat")
            outerwear.append("Insulated waterproof gloves or mittens")
            outerwear.append("Warm scarf or fleece neck gaiter")
            footwear.append("Heavy insulated snow boots with good traction")
        elif 32 <= temp_f < 50:
            clothing.append("Long-sleeve thermal base layer or shirt")
            clothing.append("Cozy sweater, thick cardigan, or heavy hoodie")
            clothing.append("Durable pants (jeans, chinos, or cords)")
            outerwear.append("Medium jacket, trench coat, or wool coat")
            if temp_f < 40 or wind_speed > 12:
                outerwear.append("Light knit gloves & beanie")
            footwear.append("Closed-toe leather boots or sturdy shoes")
        elif 50 <= temp_f < 68:
            clothing.append("Standard t-shirt, polo, or light long-sleeve shirt")
            clothing.append("Light sweater, cardigan, or zip-up hoodie")
            clothing.append("Pants, jeans, or thick leggings")
            outerwear.append(
                "Light jacket, denim jacket, windbreaker, or bomber jacket"
            )
            footwear.append("Sneakers, flat shoes, or light ankle boots")
        elif 68 <= temp_f < 80:
            clothing.append("Lightweight short-sleeve shirt, linen top, or polo")
            clothing.append("Shorts, skirt, or lightweight trousers")
            footwear.append("Breathable canvas sneakers, loafers, or sandals")
        else:  # >= 80
            clothing.append(
                "Loose, light-colored, and highly breathable fabrics (linen/cotton)"
            )
            clothing.append("Shorts, short skirt, or light summer dress")
            footwear.append(
                "Open-toed sandals, flip-flops, or ultra-breathable mesh shoes"
            )

        # 2. Feels-like comparison adjustments
        diff = feels_like_f - temp_f
        if diff <= -8:
            warnings.append(
                f"Significant wind chill! It feels {abs(diff):.1f}°F colder than actual. Add an extra wind-blocking layer."
            )
        elif diff >= 5 and temp_f >= 75:
            warnings.append(
                f"High heat index! It feels {diff:.1f}°F warmer and muggier than actual. Hydrate often and limit heavy exertion."
            )

        # 3. Wind speed adjustments
        if wind_speed > 15:
            if "Windbreaker or wind-resistant outer shell" not in outerwear:
                outerwear.append("Windbreaker or wind-resistant shell jacket")
            if wind_speed > 25:
                warnings.append(
                    "Gale force gusts! Secure loose items; umbrellas are highly likely to flip."
                )

        # 4. Precipitation and Snow adjustments
        has_snow = (
            "snow" in desc_lower or "sleet" in desc_lower or "blizzard" in desc_lower
        )
        has_rain = (
            "rain" in desc_lower
            or "shower" in desc_lower
            or "drizzle" in desc_lower
            or "thunderstorm" in desc_lower
        )
        has_precip = precip_prob > 25 or precip_rate > 0 or has_snow or has_rain

        if has_precip:
            if has_snow or (temp_f <= 32 and precip_prob > 20):
                gear.append("Water-resistant backpack/bag cover")
                warnings.append(
                    "Slippery snow/ice underfoot. Walk carefully and choose high-traction footwear."
                )
                if "Heavy insulated snow boots with good traction" not in footwear:
                    footwear.append("Insulated waterproof snow/winter boots")
            else:
                outerwear.append("Waterproof rain jacket, rain shell, or poncho")
                gear.append("Compact, windproof umbrella")
                footwear.append("Water-resistant boots or treated waterproof sneakers")
                warnings.append(
                    "Wet conditions. Avoid denim/cotton which hold water; choose synthetic fabrics."
                )

        # 5. UV Index adjustments
        if uv_index >= 3:
            gear.append("Broad-spectrum sunscreen (SPF 30+)")
            gear.append("UV-protective sunglasses")
            if uv_index >= 6:
                gear.append("Wide-brimmed sun hat or baseball cap")
                warnings.append(
                    "Very high UV index. Reapply sunscreen every 2 hours and seek shade between 10 AM and 4 PM."
                )

        # 6. Humidity adjustments
        if humidity > 80 and temp_f >= 75:
            comfort_notes.append(
                "High humidity prevents sweat evaporation. Wear moisture-wicking activewear."
            )
        elif humidity < 20:
            comfort_notes.append(
                "Extremely dry air. Carry moisturizing lotion and lip balm."
            )

        return {
            "clothing": list(dict.fromkeys(clothing)),
            "outerwear": list(dict.fromkeys(outerwear)),
            "footwear": list(dict.fromkeys(footwear)),
            "gear": list(dict.fromkeys(gear)),
            "warnings": list(dict.fromkeys(warnings)),
            "comfort_notes": list(dict.fromkeys(comfort_notes)),
        }
