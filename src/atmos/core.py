import requests
import json
from typing import Tuple, List, Dict, Any
from datetime import datetime
from atmos.config import settings
from atmos.models import (
    CurrentConditions,
    Temperature,
    Wind,
    Precipitation,
    HourlyHistoryItem,
    HourlyForecastItem,
    DailyForecastItem,
    WeatherAlert,
)
from atmos.exceptions import AtmosAPIError
from atmos.cache import cache_manager
from rich.console import Console

console = Console()


class AtmosClient:
    """
    Client for the Google Maps Platform Weather API.
    """

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://weather.googleapis.com/v1"
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def _check_api_key(self):
        if not self.api_key:
            raise ValueError(
                "GOOGLE_MAPS_API_KEY is not set. Please check your configuration."
            )

    def _handle_error(self, resp: requests.Response):
        """Parses API error responses into AtmosAPIError."""
        try:
            data = resp.json()
            err_obj = data.get("error", {})
            msg = err_obj.get("message", resp.text)

            # Common handling
            if resp.status_code == 404:
                msg = "Weather data is not available for this location."
            elif resp.status_code == 403:
                msg = "API Key invalid or permission denied. Check your GCP Console."
            elif resp.status_code == 400:
                msg = f"Invalid request: {msg}"

        except Exception:
            msg = resp.text

        raise AtmosAPIError(resp.status_code, msg, resp.text)

    def geocode(self, location: str) -> Tuple[float, float, str]:
        """Resolves a location to (lat, lng, formatted_address) using the Google Maps Geocoding API."""
        self._check_api_key()
        params = {"address": location, "key": self.api_key}
        resp = requests.get(self.geocode_url, params=params, timeout=10.0)

        if not resp.ok:
            self._handle_error(resp)

        data = resp.json()
        status = data.get("status")

        if status == "ZERO_RESULTS":
            raise ValueError(f"Location not found: {location}")
        elif status != "OK" and status is not None:
            err_msg = data.get("error_message", "Unknown geocoding error")
            raise AtmosAPIError(
                200, f"Geocoding API Error ({status}): {err_msg}", json.dumps(data)
            )

        if not data.get("results"):
            raise ValueError(f"Location not found: {location}")

        result = data["results"][0]
        loc = result["geometry"]["location"]
        lat_lng = (loc["lat"], loc["lng"])
        formatted_address = result.get("formatted_address", location)

        # Cache the result for 24 hours (86400 seconds)
        loc_key = f"coords_{location.lower().strip()}"
        cache_manager.set(loc_key, lat_lng, expires_sec=86400)

        return lat_lng[0], lat_lng[1], formatted_address

    def get_coords(self, location: str) -> Tuple[float, float]:
        """Resolves a string location to (lat, lng), utilizing caching and offline fallback."""
        from atmos.places import places_manager

        # Instantly resolve coordinates of saved places if pre-cached
        saved_coords = places_manager.get_coords(location)
        if saved_coords is not None:
            return saved_coords

        # Check if it's a saved place but with a custom address
        saved_address = places_manager.get(location)
        lookup_name = saved_address if saved_address else location

        loc_key = f"coords_{lookup_name.lower().strip()}"

        # Try to read from cache
        cached = cache_manager.get(loc_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return tuple(val)  # type: ignore

        # If not cached or expired, fetch from API
        try:
            lat, lng, _ = self.geocode(lookup_name)
            return lat, lng
        except Exception as e:
            # If API request fails, check if we have expired cache to fall back on
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Geocoding connection failed. Using cached coordinates from {age_min} minutes ago.[/yellow]"
                )
                return tuple(val)  # type: ignore
            raise e

    def _parse_condition(
        self, data: Dict[str, Any]
    ) -> Tuple[Temperature, Temperature, Wind, Precipitation, str, float, float]:
        """Helper to parse common fields from a data block (current or history)."""
        if data is None:
            data = {}

        # Temperature
        temp_obj = data.get("temperature", {})
        temp = Temperature(
            value=temp_obj.get("degrees", 0.0), units=temp_obj.get("unit", "CELSIUS")
        )

        feels_like_obj = data.get("feelsLikeTemperature", {})
        feels_like = Temperature(
            value=feels_like_obj.get("degrees", 0.0),
            units=feels_like_obj.get("unit", "CELSIUS"),
        )

        # Wind
        wind_obj = data.get("wind", {})
        speed_obj = wind_obj.get("speed", {})
        gust_obj = wind_obj.get("gust", {})
        direction_obj = wind_obj.get("direction", {})

        wind = Wind(
            speed=speed_obj.get("value", 0.0),
            direction=direction_obj.get("cardinal", "N"),
            gust=gust_obj.get("value", 0.0),
        )

        # Precipitation
        precip_obj = data.get("precipitation", {})
        prob_obj = precip_obj.get("probability", {})
        qpf_obj = precip_obj.get("qpf", {})

        precip = Precipitation(
            type=prob_obj.get("type", "None"),
            rate=qpf_obj.get("quantity", 0.0),
            probability=prob_obj.get("percent", 0.0),
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
        """Fetches real current weather conditions, with caching and offline fallback."""
        try:
            lat, lng = self.get_coords(location)
        except Exception as e:
            # If coordinates lookup fails, let's see if we have cached current weather
            # using the location name directly as an alias.
            loc_key = f"coords_{location.lower().strip()}"
            cached_loc = cache_manager.get(loc_key)
            if cached_loc:
                val, _, _ = cached_loc
                lat, lng = val
            else:
                raise e

        cache_key = f"current_{lat}_{lng}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return CurrentConditions.model_validate(val)

        try:
            url = f"{self.base_url}/currentConditions:lookup"
            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "key": self.api_key,
                "unitsSystem": "IMPERIAL",
            }

            resp = requests.get(url, params=params, timeout=10.0)

            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            cond = data.get("currentConditions", data)

            temp, feels_like, wind, precip, desc, humidity, pressure = (
                self._parse_condition(cond)
            )

            # Visibility
            vis_obj = cond.get("visibility", {})
            vis_val = vis_obj.get("distance", 10.0)

            result = CurrentConditions(
                temperature=temp,
                feels_like=feels_like,
                humidity=humidity,
                description=desc,
                wind=wind,
                precipitation=precip,
                uv_index=cond.get("uvIndex", 0),
                visibility=vis_val,
                pressure=pressure,
            )

            # Cache successful result for 10 minutes (600 seconds)
            cache_manager.set(
                cache_key, result.model_dump(mode="json"), expires_sec=600
            )
            return result
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached current conditions from {age_min} minutes ago.[/yellow]"
                )
                return CurrentConditions.model_validate(val)
            raise e

    def get_hourly_history(
        self, location: str, hours: int = 24
    ) -> List[HourlyHistoryItem]:
        """Fetches hourly history for the last N hours, with caching and offline fallback."""
        try:
            lat, lng = self.get_coords(location)
        except Exception as e:
            loc_key = f"coords_{location.lower().strip()}"
            cached_loc = cache_manager.get(loc_key)
            if cached_loc:
                val, _, _ = cached_loc
                lat, lng = val
            else:
                raise e

        cache_key = f"history_{lat}_{lng}_{hours}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return [HourlyHistoryItem.model_validate(item) for item in val]

        try:
            url = f"{self.base_url}/history/hours:lookup"
            fetch_hours = min(hours, 24)

            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "hours": fetch_hours,
                "key": self.api_key,
                "unitsSystem": "IMPERIAL",
                "pageSize": fetch_hours,
            }

            resp = requests.get(url, params=params, timeout=10.0)
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()

            history_items = []
            entries = data.get("historyHours", [])

            for entry in entries:
                interval = entry.get("interval", {})
                ts_str = interval.get("startTime")
                if not ts_str:
                    continue

                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                temp, feels_like, wind, precip, desc, humidity, pressure = (
                    self._parse_condition(entry)
                )

                item = HourlyHistoryItem(
                    timestamp=ts,
                    temperature=temp,
                    feels_like=feels_like,
                    humidity=humidity,
                    description=desc,
                    wind=wind,
                    precipitation=precip,
                    pressure=pressure,
                )
                history_items.append(item)

            # Cache successful result for 1 hour (3600 seconds)
            cache_manager.set(
                cache_key,
                [item.model_dump(mode="json") for item in history_items],
                expires_sec=3600,
            )
            return history_items
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached hourly history from {age_min} minutes ago.[/yellow]"
                )
                return [HourlyHistoryItem.model_validate(item) for item in val]
            raise e

    def get_hourly_forecast(
        self, location: str, hours: int = 24
    ) -> List[HourlyForecastItem]:
        """Fetches hourly forecast, with caching and offline fallback."""
        try:
            lat, lng = self.get_coords(location)
        except Exception as e:
            loc_key = f"coords_{location.lower().strip()}"
            cached_loc = cache_manager.get(loc_key)
            if cached_loc:
                val, _, _ = cached_loc
                lat, lng = val
            else:
                raise e

        cache_key = f"hourly_{lat}_{lng}_{hours}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return [HourlyForecastItem.model_validate(item) for item in val]

        try:
            url = f"{self.base_url}/forecast/hours:lookup"

            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "hours": min(hours, 240),
                "key": self.api_key,
                "unitsSystem": "IMPERIAL",
                "pageSize": min(hours, 24),
            }

            resp = requests.get(url, params=params, timeout=10.0)
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            entries = data.get("forecastHours", [])

            items = []
            for entry in entries:
                interval = entry.get("interval", {})
                ts_str = interval.get("startTime")
                if not ts_str:
                    continue

                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                temp, feels_like, wind, precip, desc, humidity, pressure = (
                    self._parse_condition(entry)
                )

                items.append(
                    HourlyForecastItem(
                        timestamp=ts,
                        temperature=temp,
                        feels_like=feels_like,
                        humidity=humidity,
                        description=desc,
                        wind=wind,
                        precipitation=precip,
                        pressure=pressure,
                    )
                )

            # Cache successful result for 15 minutes (900 seconds)
            cache_manager.set(
                cache_key,
                [item.model_dump(mode="json") for item in items],
                expires_sec=900,
            )
            return items
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached hourly forecast from {age_min} minutes ago.[/yellow]"
                )
                return [HourlyForecastItem.model_validate(item) for item in val]
            raise e

    def get_daily_forecast(
        self, location: str, days: int = 5
    ) -> List[DailyForecastItem]:
        """Fetches daily forecast, with caching and offline fallback."""
        try:
            lat, lng = self.get_coords(location)
        except Exception as e:
            loc_key = f"coords_{location.lower().strip()}"
            cached_loc = cache_manager.get(loc_key)
            if cached_loc:
                val, _, _ = cached_loc
                lat, lng = val
            else:
                raise e

        cache_key = f"daily_{lat}_{lng}_{days}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return [DailyForecastItem.model_validate(item) for item in val]

        try:
            url = f"{self.base_url}/forecast/days:lookup"

            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "days": min(days, 10),
                "pageSize": min(days, 10),  # Added pageSize
                "key": self.api_key,
                "unitsSystem": "IMPERIAL",
            }

            resp = requests.get(url, params=params, timeout=10.0)
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            entries = data.get("forecastDays", [])

            items = []
            for entry in entries:
                interval = entry.get("interval", {})
                ts_str = interval.get("startTime")
                if not ts_str:
                    continue

                date = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

                low_obj = entry.get("minTemperature", {})
                high_obj = entry.get("maxTemperature", {})

                low_temp = Temperature(
                    value=low_obj.get("degrees", 0.0),
                    units=low_obj.get("unit", "CELSIUS"),
                )
                high_temp = Temperature(
                    value=high_obj.get("degrees", 0.0),
                    units=high_obj.get("unit", "CELSIUS"),
                )

                day_forecast = entry.get("daytimeForecast")
                night_forecast = entry.get("nighttimeForecast")
                target_forecast = day_forecast or night_forecast or {}

                cond_obj = target_forecast.get("weatherCondition", {})
                desc_obj = cond_obj.get("description", {})
                desc = desc_obj.get("text", cond_obj.get("type", "Unknown"))

                day_precip = target_forecast.get("precipitation", {})
                prob = day_precip.get("probability", {}).get("percent", 0.0)

                cloud_cover = target_forecast.get("cloudCover", 0)

                # Wind parsing
                wind_obj = target_forecast.get("wind", {})
                speed_obj = wind_obj.get("speed", {})
                gust_obj = wind_obj.get("gust", {})
                direction_obj = wind_obj.get("direction", {})

                max_wind = Wind(
                    speed=speed_obj.get("value", 0.0),
                    direction=direction_obj.get("cardinal", "N"),
                    gust=gust_obj.get("value", 0.0),
                )

                sun_obj = entry.get("sunEvents", {})
                sunrise_str = sun_obj.get("sunriseTime")
                sunset_str = sun_obj.get("sunsetTime")

                sunrise = (
                    datetime.fromisoformat(sunrise_str.replace("Z", "+00:00"))
                    if sunrise_str
                    else None
                )
                sunset = (
                    datetime.fromisoformat(sunset_str.replace("Z", "+00:00"))
                    if sunset_str
                    else None
                )

                # Moon Parsing
                moon_obj = entry.get("moonEvents", {})
                moon_phase = moon_obj.get("moonPhase", "Unknown")

                moonrise_list = moon_obj.get("moonriseTimes", [])
                moonrise = (
                    datetime.fromisoformat(moonrise_list[0].replace("Z", "+00:00"))
                    if moonrise_list
                    else None
                )

                moonset_list = moon_obj.get("moonsetTimes", [])
                moonset = (
                    datetime.fromisoformat(moonset_list[0].replace("Z", "+00:00"))
                    if moonset_list
                    else None
                )

                items.append(
                    DailyForecastItem(
                        date=date,
                        low_temp=low_temp,
                        high_temp=high_temp,
                        description=desc,
                        precipitation_probability=prob,
                        sunrise=sunrise,
                        sunset=sunset,
                        moon_phase=moon_phase,
                        moonrise=moonrise,
                        moonset=moonset,
                        cloud_cover=cloud_cover,
                        max_wind=max_wind,
                    )
                )

            # Cache successful result for 30 minutes (1800 seconds)
            cache_manager.set(
                cache_key,
                [item.model_dump(mode="json") for item in items],
                expires_sec=1800,
            )
            return items
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached daily forecast from {age_min} minutes ago.[/yellow]"
                )
                return [DailyForecastItem.model_validate(item) for item in val]
            raise e

    def get_public_alerts(self, location: str) -> List[WeatherAlert]:
        """Fetches active weather alerts, with caching and offline fallback."""
        try:
            lat, lng = self.get_coords(location)
        except Exception as e:
            loc_key = f"coords_{location.lower().strip()}"
            cached_loc = cache_manager.get(loc_key)
            if cached_loc:
                val, _, _ = cached_loc
                lat, lng = val
            else:
                raise e

        cache_key = f"alerts_{lat}_{lng}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return [WeatherAlert.model_validate(item) for item in val]

        try:
            url = f"{self.base_url}/publicAlerts:lookup"

            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "key": self.api_key,
            }

            resp = requests.get(url, params=params, timeout=10.0)
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            alerts_data = data.get("alerts", [])

            items = []
            for a in alerts_data:
                headline = a.get("headline", "Alert")
                desc = a.get("description", "")
                severity = a.get("severity", "UNKNOWN")
                urgency = a.get("urgency", "UNKNOWN")
                certainty = a.get("certainty", "UNKNOWN")
                event_type = a.get("event", "Unknown Event")
                source = a.get("senderName", "Unknown Source")

                start_str = a.get("effective")
                end_str = a.get("expires")

                start = (
                    datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_str
                    else None
                )
                end = (
                    datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    if end_str
                    else None
                )

                items.append(
                    WeatherAlert(
                        headline=headline,
                        description=desc,
                        type=event_type,
                        severity=severity,
                        urgency=urgency,
                        certainty=certainty,
                        start_time=start,
                        end_time=end,
                        source=source,
                    )
                )

            # Cache successful result for 5 minutes (300 seconds)
            cache_manager.set(
                cache_key,
                [item.model_dump(mode="json") for item in items],
                expires_sec=300,
            )
            return items
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached public alerts from {age_min} minutes ago.[/yellow]"
                )
                return [WeatherAlert.model_validate(item) for item in val]
            raise e

    def generate_ai_briefing(self, context_data: Dict[str, Any]) -> str:
        """Generates a natural-language weather briefing using Google Gemini API."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            import os

            api_key = (
                os.environ.get("GEMINI_API_KEY")
                or "AIzaSyDgnBTB9UI-qbtRVzuJIQiwV0g_wsin8iQ"
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={api_key}"

        prompt = (
            "You are Atmos Intelligence, a professional weather advisor.\n"
            "Below is a JSON dump of the weather conditions, forecast, severe alerts, and activity scores for a location.\n"
            "Please write a beautifully formatted, natural, engaging, and hyper-personalized daily weather briefing.\n"
            "Start with a warm greeting, summarize the current conditions, and highlights of the forecast.\n"
            "Explicitly call out any active severe alerts (with urgency/warnings), exceptionally high or low outdoor activity scores,\n"
            "and night-sky stargazing conditions. Suggest appropriate clothing or precautions.\n"
            "Keep the tone professional, helpful, and concise. Use clean markdown formatting (bullet points, bold highlights) suitable for terminal display.\n\n"
            f"WEATHER DATA CONTEXT:\n{json.dumps(context_data, indent=2, default=str)}"
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            },
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if not resp.ok:
                return f"[yellow]Failed to generate briefing from Gemini API (HTTP {resp.status_code}): {resp.text}[/yellow]"

            resp_data = resp.json()
            candidates = resp_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "No text generated.")
            return "[yellow]No briefing response candidates generated from Gemini.[/yellow]"
        except Exception as e:
            return f"[red]Error calling Gemini API: {e}[/red]"

    def get_hourly_forecast_by_coords(
        self, lat: float, lng: float, hours: int = 24
    ) -> List[HourlyForecastItem]:
        """Fetches hourly forecast using exact lat/lng coordinates, with caching and offline fallback."""
        self._check_api_key()
        cache_key = f"hourly_{lat}_{lng}_{hours}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return [HourlyForecastItem.model_validate(item) for item in val]

        try:
            url = f"{self.base_url}/forecast/hours:lookup"

            params = {
                "location.latitude": lat,
                "location.longitude": lng,
                "hours": min(hours, 240),
                "key": self.api_key,
                "unitsSystem": "IMPERIAL",
                "pageSize": min(hours, 24),
            }

            resp = requests.get(url, params=params, timeout=10.0)
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            entries = data.get("forecastHours", [])

            items = []
            for entry in entries:
                interval = entry.get("interval", {})
                ts_str = interval.get("startTime")
                if not ts_str:
                    continue

                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                temp, feels_like, wind, precip, desc, humidity, pressure = (
                    self._parse_condition(entry)
                )

                items.append(
                    HourlyForecastItem(
                        timestamp=ts,
                        temperature=temp,
                        feels_like=feels_like,
                        humidity=humidity,
                        description=desc,
                        wind=wind,
                        precipitation=precip,
                        pressure=pressure,
                    )
                )

            # Cache successful result for 15 minutes (900 seconds)
            cache_manager.set(
                cache_key,
                [item.model_dump(mode="json") for item in items],
                expires_sec=900,
            )
            return items
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Weather API connection failed. Using cached hourly forecast from {age_min} minutes ago.[/yellow]"
                )
                return [HourlyForecastItem.model_validate(item) for item in val]
            raise e

    def get_route_directions(self, start: str, end: str) -> Dict[str, Any]:
        """Queries Google Directions API to fetch route details, with caching and offline fallback."""
        self._check_api_key()
        cache_key = f"route_{start.lower().strip()}_{end.lower().strip()}"
        cached = cache_manager.get(cache_key)
        if cached:
            val, is_expired, age_sec = cached
            if not is_expired:
                return val  # type: ignore

        try:
            params = {
                "origin": start,
                "destination": end,
                "key": self.api_key,
            }
            resp = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=params,
                timeout=10.0,
            )
            if not resp.ok:
                self._handle_error(resp)

            data = resp.json()
            if data.get("status") not in ("OK", None):
                raise ValueError(
                    f"Directions API error: {data.get('status')} - {data.get('error_message', '')}"
                )

            # Cache successful result for 24 hours (86400 seconds)
            cache_manager.set(cache_key, data, expires_sec=86400)
            return data
        except Exception as e:
            if cached:
                val, _, age_sec = cached
                age_min = age_sec // 60
                console.print(
                    f"[yellow]⚠️ Directions API connection failed. Using cached route from {age_min} minutes ago.[/yellow]"
                )
                return val  # type: ignore
            raise e

    def get_route_weather(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Calculates waypoints along a driving route and fetches weather forecasts at their estimated arrival times (ETAs)."""
        data = self.get_route_directions(start, end)
        routes = data.get("routes", [])
        if not routes:
            raise ValueError(f"No routes found between {start} and {end}.")

        legs = routes[0].get("legs", [])
        if not legs:
            raise ValueError("No legs found in route.")

        leg = legs[0]
        start_address = leg.get("start_address", start)
        end_address = leg.get("end_address", end)
        steps = leg.get("steps", [])

        waypoints = []
        # Add the starting waypoint
        waypoints.append(
            {
                "lat": leg["start_location"]["lat"],
                "lng": leg["start_location"]["lng"],
                "address": start_address,
                "instruction": "Departure",
                "elapsed_seconds": 0,
                "distance_text": "0.0 mi",
            }
        )

        current_elapsed = 0
        last_sampled_elapsed = 0
        # Sample waypoints every 2 hours of driving time (7200 seconds)
        sample_interval = 7200

        for step in steps:
            step_duration = step.get("duration", {}).get("value", 0)
            current_elapsed += step_duration

            if current_elapsed - last_sampled_elapsed >= sample_interval:
                waypoints.append(
                    {
                        "lat": step["start_location"]["lat"],
                        "lng": step["start_location"]["lng"],
                        "address": step.get("html_instructions", "Waypoint")
                        .replace("<b>", "")
                        .replace("</b>", "")
                        .replace('<div style="font-size:0.9em">', " - ")
                        .replace("</div>", ""),
                        "instruction": "Driving waypoint",
                        "elapsed_seconds": current_elapsed,
                        "distance_text": step.get("distance", {}).get("text", "0.0 mi"),
                    }
                )
                last_sampled_elapsed = current_elapsed

        # Add destination waypoint
        waypoints.append(
            {
                "lat": leg["end_location"]["lat"],
                "lng": leg["end_location"]["lng"],
                "address": end_address,
                "instruction": "Arrival",
                "elapsed_seconds": current_elapsed,
                "distance_text": "Arrival",
            }
        )

        results = []
        start_time = datetime.now()

        for wp in waypoints:
            lat = wp["lat"]
            lng = wp["lng"]
            elapsed = wp["elapsed_seconds"]

            from datetime import timedelta

            eta = start_time + timedelta(seconds=elapsed)

            # Determine forecast hours into the future
            hours_ahead = max(1, round(elapsed / 3600))
            fetch_hours = max(24, hours_ahead + 4)

            try:
                forecast_items = self.get_hourly_forecast_by_coords(
                    lat, lng, hours=fetch_hours
                )

                # Match closest forecast item to the ETA
                target_item = None
                min_diff = None
                for item in forecast_items:
                    from datetime import timezone

                    eta_utc = eta.astimezone(timezone.utc)
                    diff = abs((item.timestamp - eta_utc).total_seconds())
                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        target_item = item

                results.append({"waypoint": wp, "eta": eta, "weather": target_item})
            except Exception as e:
                results.append(
                    {"waypoint": wp, "eta": eta, "weather": None, "error": str(e)}
                )

        return results


# Global client instance
client = AtmosClient()
