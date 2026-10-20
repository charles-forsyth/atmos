# Atmos

> **A CLI weather intelligence tool (`v0.1.46`) powered by the Google Maps Platform Weather API and Google Gemini.**

Atmos brings real-time weather observations, 10-day / 240-hour forecasts, 24-hour history, severe weather alerts, ASCII trend charts, astronomy/stargazing scores, outdoor activity planners, route weather corridors, and AI weather briefings directly to your terminal.

See [SPEC.md](SPEC.md) for the full system specification, architecture, caching/offline fallback design, and requirement traceability.

## Features

* **Current Conditions (`atmos [LOCATION]`):** Real-time temperature, feels-like, wind speed/direction, humidity, UV index, visibility, and pressure.
* **Forecasts (`atmos forecast`):** 10-day daily summary and 240-hour hourly detail (`--hourly`).
* **AI Weather Briefing (`atmos brief`):** Personalized daily briefing, activity scores, stargazing outlook, and wardrobe guidance generated via `gemini-3.1-pro`.
* **History (`atmos history`):** Look back at the past 24 hours of hourly weather observations.
* **Alerts (`atmos alert`):** Check for active severe weather warnings.
* **ASCII Charts (`atmos graph`):** Terminal line charts for `temp`, `precip`, `wind`, and `humidity` trends.
* **Astronomy (`atmos stars`):** Sunrise, sunset, moon phase/illumination, and stargazing suitability score.
* **Smart Activity Planner (`atmos find`):** Ranks upcoming days (0–100) for `hiking`, `running`, `bbq`, `camping`, `beach`, or `stargazing`.
* **Wardrobe & Gear (`atmos wardrobe`):** Layering and gear recommendations tailored to current and forecast conditions.
* **Multi-City Compare & Route Weather (`atmos compare`, `atmos route`):** Side-by-side city comparisons and weather along a driving route.
* **Saved Places & Offline Cache (`atmos places`):** Save aliases (`home`, `work`) in `~/.config/atmos/places.json` with automatic offline cache fallback (`~/.config/atmos/cache.json`).

## Installation

Install using `uv`:

```bash
uv tool install --python 3.12 git+https://github.com/charles-forsyth/atmos.git
```

To update:

```bash
uv tool upgrade atmos
```

## Configuration

Create `~/.config/atmos/.env` (`chmod 600`) with your Google Maps Platform API key (Weather, Geocoding, and Routes APIs enabled) and Gemini API key (for `atmos brief`):

```env
GOOGLE_MAPS_API_KEY=your_maps_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### 1. Current Weather & AI Briefing
```bash
atmos "New York"
atmos brief "Seattle, WA"
```

### 2. Forecasts & History
```bash
atmos forecast -L "London"
atmos forecast -L "Seattle" --hourly -H 24
atmos history -L "Chicago" -H 12
```

### 3. Visualization, Astronomy & Activity Planning
```bash
atmos graph -L "Boston" --metric temp --hours 48
atmos stars -L "Joshua Tree, CA"
atmos find -L "San Francisco" --activity hiking
atmos wardrobe -L "Denver, CO"
```

### 4. Multi-City Compare, Route Weather & Live Dashboard
```bash
atmos compare "New York" "Chicago" "Los Angeles" --forecast
atmos route "Boston, MA" "Portland, ME"
atmos dashboard "New York"
```

### 5. Saved Places
```bash
atmos places add home "123 Main St, Springfield"
atmos places add work "Empire State Building, NY"
atmos home
atmos places list
```

## Development

```bash
uv sync --python 3.12
uv run --python 3.12 pytest
uv run --python 3.12 ruff check .
```
