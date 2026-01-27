from datetime import datetime
from typing import Annotated

import httpx
from fastmcp import FastMCP

from config import settings
from logger import get_configured_logger

logger = get_configured_logger("weather-mcp")

mcp = FastMCP("OpenWeatherMap")

API_KEY = settings.open_weather_api_key
BASE_URL = settings.openweather_base_url
HISTORIC_BASE_URL = settings.openweather_historic_base_url


def kelvin_to_celsius(kelvin: float) -> float:
    return kelvin - 273.15


def geocode_city(city: str) -> tuple[float, float] | None:
    url = f"{BASE_URL}/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": API_KEY}

    logger.debug(f"Geocoding: {city}")
    response = httpx.get(url, params=params)
    if response.status_code != 200:
        logger.warning(f"Geocoding failed: {response.status_code}")
        return None

    data = response.json()
    if not data:
        logger.warning(f"No geocoding results for: {city}")
        return None

    lat, lon = data[0]["lat"], data[0]["lon"]
    logger.debug(f"Geocoded {city} to ({lat}, {lon})")
    return lat, lon


@mcp.tool(description="Get daily weather forecast for a city (up to 16 days ahead)")
def get_daily_forecast(
    city: Annotated[str, "Name of the city"],
    days_ahead: Annotated[int, "Number of days ahead (1-16)"] = 7,
) -> str:
    logger.info(f"Fetching daily forecast for {city}, {days_ahead} days")

    coords = geocode_city(city)
    if not coords:
        logger.warning(f"Location not found: {city}")
        return f"Could not find location: {city}"

    lat, lon = coords
    days_ahead = max(1, min(16, days_ahead))

    url = f"{BASE_URL}/data/2.5/forecast/daily"
    params = {
        "lat": lat,
        "lon": lon,
        "cnt": days_ahead,
        "appid": API_KEY,
        "units": "metric",
    }

    response = httpx.get(url, params=params)
    if response.status_code != 200:
        logger.warning("Daily forecast API unavailable")
        logger.debug(response)
        logger.debug(response.json())
        logger.debug(url)
        return {"error": "Daily forecast API unavailable"}
    seen_dates = set()
    data = response.json()
    forecasts = []
    for item in data.get("list", []):
        date_unix_timestamp = item["dt"]
        date = datetime.fromtimestamp(date_unix_timestamp).strftime("%Y-%m-%d")
        if date not in seen_dates and len(seen_dates) < days_ahead:
            seen_dates.add(date)
            weather = item["weather"][0]["description"]
            temp = item["temp"]["day"]
            feels_like_temp = item["feels_like"]["day"]
            humidity = item["humidity"]
            forecasts.append(
                f"  {date}: {weather}, {temp:.1f}°C, feels like {feels_like_temp:.1f}°C, humidity {humidity}%"
            )

    logger.info(f"Returning {len(forecasts)} forecast days for {city}")
    return f"Weather forecast for {city}:\n" + "\n".join(forecasts)


@mcp.tool(description="Get average monthly weather for a city (for long-term planning)")
def get_monthly_average(
    city: Annotated[str, "Name of the city"],
    month: Annotated[int, "Month number (1-12)"] = None,
) -> str:
    logger.info(f"Fetching monthly average for city={city}, month={month}")

    coords = geocode_city(city)
    if not coords:
        logger.warning(f"Location not found: {city}")
        return f"Could not find location: {city}"

    if month is None:
        month = datetime.now().month

    month = max(1, min(12, month))
    lat, lon = coords

    url = f"{HISTORIC_BASE_URL}/data/2.5/aggregated/month"
    params = {
        "lat": lat,
        "lon": lon,
        "month": month,
        "appid": API_KEY,
        "units": "metric",
    }

    response = httpx.get(url, params=params)

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    if response.status_code != 200:
        logger.warning("Climate API unavailable")
        logger.debug(response)
        logger.debug(response.json())
        logger.debug(url)
        return {"error": "Climate API unavailable"}

    data = response.json()
    weather_data = data.get("result", {})
    logger.info(f"Data returned from api: {data}")
    temp_avg = kelvin_to_celsius(weather_data.get("temp", {}).get("mean", "N/A"))
    temp_min = kelvin_to_celsius(weather_data.get("temp", {}).get("record_min", "N/A"))
    temp_max = kelvin_to_celsius(weather_data.get("temp", {}).get("record_max", "N/A"))
    humidity_mean = weather_data.get("humidity", {}).get("mean", "N/A")
    wind_mean = weather_data.get("wind", {}).get("mean", "N/A")
    sunshine_hours = weather_data.get("sunshine_hours")

    logger.info(f"Returning climate data for {city} in {month_names[month - 1]}")
    return (
        f"Average weather for {city} in {month_names[month - 1]}:\n"
        f"  Average temperature: {temp_avg:.2f}°C\n"
        f"  Temperature range: {temp_min:.2f}°C to {temp_max:.2f}°C\n"
        f"  Average humidity: {humidity_mean:.2f}%\n"
        f"  Average wind speed: {wind_mean:.2f} m/s\n"
        f"  Average sunshine hours: {sunshine_hours:.2f} hours"
    )


if __name__ == "__main__":
    logger.info("Starting OpenWeatherMap MCP server on port 8001")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
