# atmos specification

Version 0.1.46 (2026-10-20; code 0.1.46). Owner: Chuck Forsyth.
Repository: `charles-forsyth/atmos` (local checkout `~/Projects/atmos`). License: MIT.

## 1. Purpose and scope

`atmos` is a terminal weather intelligence CLI powered by the **Google Maps Platform Weather API** (`weather.googleapis.com/v1`), the **Google Maps Geocoding & Routes APIs**, and **Google Gemini (`gemini-3.1-pro`)** for AI weather briefings and wardrobe recommendations. It provides:

1. **Current conditions** (`atmos [LOCATION]` or `atmos current`)
2. **10-day daily & 240-hour hourly forecasts** (`atmos forecast`)
3. **24-hour historical observations** (`atmos history`)
4. **Severe weather alerts & desktop notifications** (`atmos alert`, `atmos notify`)
5. **ASCII trend charts** (`atmos graph`)
6. **Astronomy, moon phase & stargazing scoring** (`atmos stars`)
7. **Outdoor activity scoring (`hiking`, `bbq`, `beach`, `stargazing`, `running`, `camping`)** (`atmos find`)
8. **AI weather advisor briefing** (`atmos brief`) & **AI/rule-based wardrobe recommendations** (`atmos wardrobe`)
9. **Side-by-side multi-city comparison** (`atmos compare`), **route weather corridor** (`atmos route`), and **live TUI dashboard** (`atmos dashboard`)
10. **Saved places address book** (`atmos places`) and **offline fallback cache** (`~/.config/atmos/cache.json`)

## 2. Design decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Dedicated per-tool config `~/.config/atmos/` (`0600` `.env`, `places.json`, `cache.json`) | Keeps `GOOGLE_MAPS_API_KEY` and `GEMINI_API_KEY` isolated to `atmos`, alongside persistent saved places and the response cache. |
| D2 | Two-tier caching with offline fallback (`src/atmos/cache.py`) | Weather and geocoding responses are cached in `~/.config/atmos/cache.json` with a 15-minute fresh TTL (`900s`). If a network request fails, `AtmosClient` falls back to stale cached data (marked as offline fallback) unless `--no-cache` is passed. |
| D3 | Default location resolution (`Home`) | When no location is passed on the CLI, `resolve_location()` checks `~/.config/atmos/places.json` for a saved `"Home"` (case-insensitive) entry before falling back to `"New York"`. |
| D4 | Deterministic activity & stargazing evaluators (`src/atmos/evaluator.py`) | Activity suitability scores (0–100) for hiking, running, BBQ, camping, beach, and stargazing are computed deterministically from temperature, precipitation probability, wind speed, cloud cover, UV index, and moon illumination before being passed into `atmos find` or `atmos brief`. |

## 3. Architecture

```text
atmos CLI (src/atmos/cli.py, Click command group)
  |-- Settings (src/atmos/config.py)
  |     `-- ~/.config/atmos/.env (GOOGLE_MAPS_API_KEY, GEMINI_API_KEY)
  |-- PlacesManager (src/atmos/places.py)
  |     `-- ~/.config/atmos/places.json (alias -> address resolution)
  |-- CacheManager (src/atmos/cache.py)
  |     `-- ~/.config/atmos/cache.json (TTL cache + corrupt-JSON recovery + offline fallback)
  |-- AtmosClient (src/atmos/core.py)
  |     |-- geocode()           -> maps.googleapis.com/maps/api/geocode/json
  |     |-- get_current()       -> weather.googleapis.com/v1/currentConditions:lookup
  |     |-- get_daily_forecast()-> weather.googleapis.com/v1/forecast/days:lookup
  |     |-- get_hourly_forecast()-> weather.googleapis.com/v1/forecast/hours:lookup
  |     |-- get_history()       -> weather.googleapis.com/v1/history/hours:lookup
  |     |-- get_alerts()        -> weather.googleapis.com/v1/publicAlerts:lookup
  |     `-- generate_briefing() -> google.genai (gemini-3.1-pro)
  `-- Domain Evaluators & Renderers
        |-- models.py    (Pydantic models: CurrentConditions, DailyForecastItem, HourlyForecastItem, WeatherAlert)
        |-- evaluator.py (Activity & stargazing scoring 0-100)
        |-- wardrobe.py  (Layering & gear recommendations)
        `-- cli.py       (Rich tables, panels, asciichartpy graphs, Live dashboard)
```

### Module map

| File | Responsibility |
|---|---|
| `src/atmos/cli.py` | Click CLI group (`CustomGroup` allowing bare `atmos "City"` positional invocation) and 14 subcommands (`current`, `forecast`, `history`, `alert`, `notify`, `graph`, `stars`, `find`, `brief`, `wardrobe`, `compare`, `route`, `dashboard`, `places`). |
| `src/atmos/core.py` | `AtmosClient` REST client for Google Maps Geocoding, Routes, and Weather v1 endpoints, plus Gemini briefing synthesis and Rich display helpers. |
| `src/atmos/models.py` | Pydantic data models for weather observations, forecasts, astronomy, and alerts. |
| `src/atmos/cache.py` | `CacheManager` managing `~/.config/atmos/cache.json` with TTL expiration, corruption recovery, and `ATMOS_DISABLE_CACHE` / `--no-cache` bypass. |
| `src/atmos/places.py` | `PlacesManager` CRUD over `~/.config/atmos/places.json`. |
| `src/atmos/evaluator.py` | Scoring algorithms for `hiking`, `running`, `bbq`, `camping`, `beach`, and `stargazing`. |
| `src/atmos/wardrobe.py` | Rule-based and AI-assisted clothing/gear recommendations from conditions. |
| `src/atmos/exceptions.py` | `AtmosAPIError` with HTTP status and user-actionable message translation. |
| `src/atmos/utils.py` | Unit conversions, compass directions, moon phase formatting. |

## 4. External APIs and endpoints

| Operation | Endpoint | Auth |
|---|---|---|
| Geocoding | `GET https://maps.googleapis.com/maps/api/geocode/json` | `GOOGLE_MAPS_API_KEY` |
| Current conditions | `GET https://weather.googleapis.com/v1/currentConditions:lookup` | `GOOGLE_MAPS_API_KEY` |
| Daily forecast (up to 10d) | `GET https://weather.googleapis.com/v1/forecast/days:lookup` | `GOOGLE_MAPS_API_KEY` |
| Hourly forecast (up to 240h) | `GET https://weather.googleapis.com/v1/forecast/hours:lookup` | `GOOGLE_MAPS_API_KEY` |
| Hourly history (up to 24h) | `GET https://weather.googleapis.com/v1/history/hours:lookup` | `GOOGLE_MAPS_API_KEY` |
| Public weather alerts | `GET https://weather.googleapis.com/v1/publicAlerts:lookup` | `GOOGLE_MAPS_API_KEY` |
| AI Weather Briefing | `google-genai` (`gemini-3.1-pro`) | `GEMINI_API_KEY` |

## 5. Configuration (`~/.config/atmos/`)

| File / Variable | Purpose |
|---|---|
| `~/.config/atmos/.env` | `GOOGLE_MAPS_API_KEY` (Weather + Geocoding + Routes APIs) and `GEMINI_API_KEY` (for `atmos brief`). |
| `~/.config/atmos/places.json` | JSON dictionary mapping saved place aliases (e.g. `"home"`, `"work"`) to address strings. |
| `~/.config/atmos/cache.json` | Cached API responses keyed by endpoint + coordinates with unix timestamps. |

## 6. CLI interface

```text
atmos [--version] [--no-cache] [COMMAND] [ARGS]...

Commands:
  current [LOCATION] [-L LOCATION]                  # Current weather (also default when command omitted)
  forecast [LOCATION] [-L LOCATION] [-d DAYS] [--hourly] [-H HOURS]
  history [LOCATION] [-L LOCATION] [-H HOURS]
  alert [LOCATION] [-L LOCATION]
  notify [LOCATION] [-L LOCATION]
  graph [LOCATION] [-L LOCATION] [-m {temp,precip,wind,humidity}] [-H HOURS]
  stars [LOCATION] [-L LOCATION]
  find [LOCATION] [-L LOCATION] [-a {hiking,bbq,beach,stargazing,running,camping}]
  brief [LOCATION] [-L LOCATION]
  wardrobe [LOCATION] [-L LOCATION]
  compare CITY1 CITY2 [CITY3...] [--forecast]
  route ORIGIN DESTINATION
  dashboard [LOCATION] [-L LOCATION] [-r REFRESH_SEC]
  places {add,list,remove} ...
```

## 7. Requirements traceability

| ID | Requirement | Verified by |
|---|---|---|
| REQ-CLI-1 | Bare positional `atmos "City"` routes to `current`; `-L` flag and saved place aliases resolve identically. | `tests/test_cli.py::test_cli_current_positional`, `test_cli_current_flag`, `test_cli_places_integration`, `tests/test_default_behavior.py` |
| REQ-CACHE-1 | Cache stores, expires, recovers from corrupt JSON, and honors `ATMOS_DISABLE_CACHE` / `--no-cache`. | `tests/test_cache.py::test_cache_set_and_get`, `test_cache_expiration`, `test_cache_corruption_recovery`, `test_cache_bypass_via_env` |
| REQ-OFFLINE-1 | Network failures fall back to cached weather data when available. | `tests/test_offline_fallback.py` |
| REQ-GEO-1 | Geocoding handles `ZERO_RESULTS`, `REQUEST_DENIED`, and `OVER_QUERY_LIMIT` with descriptive `AtmosAPIError` exceptions. | `tests/test_core.py::test_get_coords_zero_results`, `test_get_coords_request_denied`, `test_get_coords_over_query_limit` |
| REQ-EVAL-1 | Astronomy, alerts, wardrobe, graph, find, brief, compare, route, and notify commands render expected outputs. | `tests/test_astronomy.py`, `tests/test_alerts.py`, `tests/test_wardrobe.py`, `tests/test_cli.py` |

## 8. Known gaps and backlog

- **K1 (Confirmed):** `Settings.model_config` checks `./.env` before `~/.config/atmos/.env`; reversing the order or reading only `~/.config/atmos/.env` ensures local project `.env` files never shadow Atmos keys.
- **K2 (Confirmed):** `atmos notify` uses `notify-send` on Linux; adding macOS `osascript -e 'display notification ...'` fallback will support native desktop alert notifications on macOS.
