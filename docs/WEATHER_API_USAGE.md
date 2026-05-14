# Weather API Usage

## Overview

The Weather API provides current weather conditions and multi-day forecasts for a given latitude/longitude. It uses:

- Google Geocoding API to derive human-readable location information
- Google Weather API for current conditions and forecast data

Responses are pre-formatted for the frontend and enriched with combined location details.

---

## Base URL

Assuming the main FastAPI app mounts the weather router with prefix `/weather` (e.g. `app.include_router(weather_routes.router, prefix="/weather")`):

- Local development: `http://localhost:8000/weather`

Adjust the host/port/prefix according to your deployment.

---

## 1. Get Current Weather

**Endpoint**

- Method: `GET`
- Path: `/weather/current`

**Query Parameters**

- `lat` (float, required) – Latitude of the location
- `lon` (float, required) – Longitude of the location

**Example Request (curl)**

```bash
curl "http://localhost:8000/weather/current?lat=11.6878&lon=75.57743"
``

**Example Response (simplified)**

```json
{
  "location": "Kariyad, Kerala 673316, India",
  "location_data": {
    "short_name": "Kariyad",
    "display_name": "Kariyad",
    "formatted_address": "Kariyad, Kerala 673316, India",
    "locality": "Kariyad",
    "sublocality": "Kidanhi",
    "district": "Kannur",
    "state": "Kerala",
    "coordinates": {
      "lat": 11.6878,
      "lon": 75.57743
    }
  },
  "condition": "Partly cloudy",
  "temperature": "28 CELSIUS",
  "temperature_value": 28,
  "temperature_unit": "CELSIUS",
  "humidity": 78,
  "uv_index": 5,
  "wind_chill": "3.2 CELSIUS",
  "timestamp": "2025-11-22T10:30:46Z",
  "combined_location": "Kariyad, Kerala 673316, India"
}
```

> Note: Values above are illustrative; actual structure/fields come directly from Google Weather with minor formatting in `weather_service.format_weather`.

---

## 2. Get Weather Forecast

**Endpoint**

- Method: `GET`
- Path: `/weather/forecast`

**Query Parameters**

- `lat` (float, required) – Latitude
- `lon` (float, required) – Longitude
- `days` (int, optional, default `4`) – Number of forecast days to return

**Example Request (curl)**

```bash
curl "http://localhost:8000/weather/forecast?lat=11.6878&lon=75.57743&days=4"
```

**Example Response (simplified)**

```json
{
  "location": "Kariyad, Kerala 673316, India",
  "location_data": {
    "short_name": "Kariyad",
    "display_name": "Kariyad",
    "formatted_address": "Kariyad, Kerala 673316, India",
    "locality": "Kariyad",
    "sublocality": "Kidanhi",
    "district": "Kannur",
    "state": "Kerala",
    "coordinates": {
      "lat": 11.6878,
      "lon": 75.57743
    }
  },
  "forecast_days": 4,
  "days": [
    {
      "date": "2025-11-22",
      "day": {
        "condition": "Light rain",
        "temp_max": 29,
        "temp_min": 24,
        "humidity": 80,
        "precipitation": 60,
        "wind": {
          "speed": 3.2,
          "unit": "m/s",
          "direction": "SW"
        }
      },
      "night": {
        "condition": "Cloudy",
        "humidity": 88,
        "precipitation": 30
      },
      "sun": {
        "sunrise": "2025-11-22T00:30:00Z",
        "sunset": "2025-11-22T12:30:00Z"
      },
      "moon": {
        "phase": "Waxing gibbous",
        "rise": "2025-11-22T18:00:00Z",
        "set": "2025-11-23T06:00:00Z"
      }
    }
  ],
  "api_source": "Google Weather API"
}
```

The exact field names and values come from `weather_service.get_forecast`, which adapts Google Weather’s `forecastDays` structure to a frontend-friendly format.

---

## Error Handling

Both endpoints use standard HTTP status codes and return an error JSON body like:

```json
{
  "detail": "Error message here"
}
```

Possible error cases:

- `400` (via FastAPI) – Validation errors for missing/invalid query parameters
- `500` – Internal errors when calling external APIs or processing responses
- `502` / `504` – Upstream HTTP, connection, or timeout errors from Google APIs

See `app/services/weather_service.py` for detailed exception mapping.

---

## Logging & Debugging

All Geocoding and Weather API calls are logged via `app/utils/api_logger.py`. See `docs/API_LOGGING.md` for details.

For quick debugging during development, tail the log files in the `logs/` directory (geolocation_api.log, weather_api.log, forecast_api.log) while hitting the weather endpoints.
