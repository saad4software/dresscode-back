import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_FIELDS = ",".join(
    [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "weathercode",
        "sunrise",
        "sunset",
        "windspeed_10m_max",
    ]
)

HOURLY_FIELDS = ",".join(
    [
        "temperature_2m",
        "precipitation",
        "precipitation_probability",
        "weathercode",
        "windspeed_10m",
        "relativehumidity_2m",
    ]
)


async def fetch_weather(
    location: str, date: Optional[str] = None
) -> dict[str, Any]:
    """Tool entrypoint: geocode `location` and return forecast data.

    If `date` (ISO YYYY-MM-DD) is provided, returns the forecast for that day;
    otherwise returns current conditions plus today's daily summary.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            geo = await client.get(
                GEOCODING_URL,
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            geo.raise_for_status()
            geo_data = geo.json()
            if not geo_data.get("results"):
                return {"error": f"Could not find location: {location}"}

            place = geo_data["results"][0]
            lat = place["latitude"]
            lon = place["longitude"]
            label = place.get("name", location)

            params: dict[str, Any] = {
                "latitude": lat,
                "longitude": lon,
                "timezone": "auto",
                "daily": DAILY_FIELDS,
            }
            if date:
                params["start_date"] = date
                params["end_date"] = date
                params["hourly"] = HOURLY_FIELDS
            else:
                params["current"] = (
                    "temperature_2m,relative_humidity_2m,precipitation,weathercode"
                )

            forecast = await client.get(FORECAST_URL, params=params)
            forecast.raise_for_status()
            data = forecast.json()
    except httpx.HTTPError as exc:
        logger.warning("Weather tool HTTP error: %s", exc)
        return {"error": f"Failed to get weather data: {exc}"}
    except Exception as exc:
        logger.exception("Weather tool unexpected error")
        return {"error": f"Failed to get weather data: {exc}"}

    daily = data.get("daily", {}) or {}
    result: dict[str, Any] = {
        "location": label,
        "latitude": lat,
        "longitude": lon,
        "date": date,
        "daily": {
            "temperature_max": _first(daily.get("temperature_2m_max")),
            "temperature_min": _first(daily.get("temperature_2m_min")),
            "precipitation_sum_mm": _first(daily.get("precipitation_sum")),
            "precipitation_probability_max": _first(
                daily.get("precipitation_probability_max")
            ),
            "weather_code": _first(daily.get("weathercode")),
            "sunrise": _first(daily.get("sunrise")),
            "sunset": _first(daily.get("sunset")),
            "wind_speed_max_kmh": _first(daily.get("windspeed_10m_max")),
        },
    }

    if date:
        result["hourly"] = data.get("hourly", {})
    else:
        result["current"] = data.get("current", {})

    return result


def _first(value):
    if isinstance(value, list) and value:
        return value[0]
    return value


get_weather_declaration = {
    "name": "get_weather",
    "description": (
        "Get the weather forecast for a city. Provide a date in YYYY-MM-DD "
        "format to fetch that day's forecast (sunrise, sunset, hourly "
        "temperatures, precipitation, wind). Omit the date for current "
        "conditions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g. 'Berlin', 'Munich'.",
            },
            "date": {
                "type": "string",
                "description": (
                    "Target date in ISO format YYYY-MM-DD. Optional; "
                    "omit for current conditions."
                ),
            },
        },
        "required": ["location"],
    },
}


AVAILABLE_TOOLS = {"get_weather": fetch_weather}

TOOL_DECLARATIONS = [get_weather_declaration]
