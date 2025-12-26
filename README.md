# Atmos 🌩️

> **A professional, production-grade CLI weather tool powered by the Google Maps Platform Weather API.**

Atmos brings hyper-accurate, real-time weather data directly to your terminal with a beautiful, modern interface. It features current conditions, 10-day forecasts, historical data, severe weather alerts, visualization graphs, and smart planning tools.

## Features

*   **Current Conditions:** Real-time temperature, wind, precipitation, and visibility.
*   **Forecasts:** 10-day daily summary and 240-hour hourly detail.
*   **History:** Look back at the last 24 hours of weather data.
*   **Alerts:** Check for active severe weather warnings (Tornado, Flood, Winter Storm).
*   **Visualization:** ASCII line charts for temperature, precipitation, and wind trends.
*   **Astronomy:** Dedicated view for Sunrise, Sunset, Moon Phase, and Stargazing conditions.
*   **Smart Planning:** Find the best day for Hiking, BBQ, or Stargazing based on weather logic.
*   **Places:** Save your favorite locations (Home, Work) for quick access.

## Installation

Install directly using `uv` (recommended):

```bash
uv tool install git+https://github.com/charles-forsyth/atmos.git
```

To update to the latest version:

```bash
uv tool upgrade atmos --reinstall
```

## Configuration

Atmos requires a **Google Maps Platform API Key** with the **Weather API** enabled.

1.  **Get a Key:** Go to the [Google Cloud Console](https://console.cloud.google.com/), create a project, and enable the "Weather API".
2.  **Configure:** Create a file at `~/.config/atmos/.env` with the following content:

```env
GOOGLE_MAPS_API_KEY=your_api_key_here
```

## Usage

### 1. Basic Weather
Get current conditions for any location. You can use City names, addresses, or ZIP codes.

```bash
atmos "New York"
atmos "1600 Pennsylvania Ave NW, Washington, DC"
```

### 2. Forecasts
See what's coming up.

*   **Daily Summary (10 Days):**
    ```bash
    atmos forecast -L "London"
    ```
*   **Hourly Detail:**
    ```bash
    atmos forecast -L "Seattle" --hourly
    ```

### 3. History
Check what happened recently (up to 24 hours ago).

```bash
atmos history -L "Chicago" --hours 12
```

### 4. Severe Alerts
Check for active warnings.

```bash
atmos alert -L "Miami, FL"
```

### 5. Visualization (Graph)
Draw a trend chart in your terminal.

```bash
atmos graph -L "Boston" --metric temp
atmos graph -L "Boston" --metric precip --hours 48
```

### 6. Astronomy & Stargazing
View Sun/Moon cycles and check if tonight is good for stargazing.

```bash
atmos stars -L "Joshua Tree"
```

### 7. Smart Planning (`find`)
Let Atmos find the best day for your activity.

```bash
atmos find -L "San Francisco" --activity hiking
atmos find -L "Austin" --activity bbq
```
Supported activities: `hiking`, `bbq`, `beach`, `stargazing`, `running`.

### 8. Places Management
Save common locations to avoid typing them every time.

```bash
# Add a place
atmos places add Home "123 Main St, Springfield"
atmos places add Work "Empire State Building, NY"

# Use a place
atmos Home
atmos forecast Work

# List/Remove
atmos places list
atmos places remove Work
```

## Troubleshooting

*   **"API Error 400/404":** Ensure your API Key is valid and the **Weather API** is enabled in your Google Cloud Console.
*   **"No data returned":** Some locations (especially remote ones) might not have data for all endpoints (e.g., Alerts).
*   **Installation Issues:** Ensure you have `uv` installed. If `atmos` command is not found, ensure `~/.local/bin` is in your PATH.

## Development

Atmos follows the **Skywalker Development Workflow**.

1.  **Clone:** `git clone ...`
2.  **Sync:** `uv sync`
3.  **Run:** `uv run atmos`
4.  **Test:** `uv run pytest`
5.  **Lint:** `uv run ruff check .`