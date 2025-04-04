import asyncio
import aiohttp  # type: ignore
import os
from dotenv import load_dotenv
from typing import Dict, Any
import json

# Load API key from .env file
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# List of cities
CITIES = ["London", "New York", "Tokyo", "Paris", "Berlin", "Mumbai", "Sydney"]


def get_weather_url(city: str) -> str:
    """Construct API URL."""
    return f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"


async def fetch_weather(session: aiohttp.ClientSession, city: str) -> Dict[str, Any]:
    """Fetch weather data asynchronously."""
    try:
        async with session.get(get_weather_url(city), timeout=10) as response:
            if response.status == 200:
                return await response.json()
            return {"city": city, "error": f"Failed to fetch weather, status: {response.status}"}
    except asyncio.TimeoutError:
        return {"city": city, "error": "Timeout while fetching weather data"}
    except aiohttp.ClientError as e:
        return {"city": city, "error": f"Request failed: {str(e)}"}


async def fetch_all_weather(cities: list[str]) -> list[Dict[str, Any]]:
    """Fetch weather data for all cities asynchronously."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_weather(session, city) for city in cities]
        return await asyncio.gather(*tasks)


def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 2)


def clean_weather_data(data: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Extracts required fields from raw weather data."""
    cleaned = []
    for entry in data:
        if "main" in entry and "name" in entry:
            temp_c = entry["main"]["temp"]
            feels_like_c = entry["main"]["feels_like"]
            cleaned.append({
                "city": entry["name"],
                "temp_c": temp_c,
                "feels_like_c": feels_like_c,
                "temp_f": c_to_f(temp_c),
                "feels_like_f": c_to_f(feels_like_c)
            })
    return cleaned


async def save_to_json(data, filename: str):
    """Save data to a JSON file."""
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)


async def main():
    weather_data = await fetch_all_weather(CITIES)

    # Save full weather data
    await save_to_json(weather_data, "Weather_train.json")

    # Save cleaned weather data
    cleaned_data = clean_weather_data(weather_data)
    await save_to_json(cleaned_data, "weather_cleaned.json")


if __name__ == "__main__":
    asyncio.run(main())
