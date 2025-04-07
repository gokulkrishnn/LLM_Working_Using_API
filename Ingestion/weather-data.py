import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from typing import Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Ensure API key is loaded correctly
if not OPENWEATHER_API_KEY:
    logger.error("Missing API key. Make sure OPENWEATHER_API_KEY is set in your .env file.")
    raise ValueError("Missing API key. Make sure OPENWEATHER_API_KEY is set in your .env file.")

# List of cities
CITIES = ["London", "New York", "Tokyo", "Paris", "Berlin", "Mumbai", "Sydney"]

# Ensure Data_json directory exists
DATA_DIR = "Data_json"
os.makedirs(DATA_DIR, exist_ok=True)


def get_weather_url(city: str) -> str:
    """Construct API URL."""
    return f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"


async def fetch_weather(session: aiohttp.ClientSession, city: str) -> Dict[str, Any]:
    """Fetch weather data asynchronously with proper error handling and logging."""
    try:
        async with session.get(get_weather_url(city), timeout=10) as response:
            if response.status == 200:
                logger.info(f"Successfully fetched weather data for {city}")
                return await response.json()
            else:
                logger.warning(f"Failed to fetch weather for {city}, HTTP Status: {response.status}")
                return {"city": city, "error": f"HTTP {response.status}: Unable to fetch data"}
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching weather data for {city}")
        return {"city": city, "error": "Timeout while fetching weather data"}
    except aiohttp.ClientError as e:
        logger.error(f"Request failed for {city}: {str(e)}")
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
    """Extract required fields from raw weather data."""
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
        else:
            logger.warning(f"Incomplete data for {entry.get('city', 'unknown city')}")
    logger.info("Cleaned weather data successfully.")
    return cleaned


async def save_to_json(data, filename: str):
    """Save data to a JSON file inside Data_json directory."""
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"Data saved successfully to {file_path}")
    except IOError as e:
        logger.error(f"Failed to save data to {file_path}: {str(e)}")


async def main():
    logger.info("Starting weather data fetch...")
    weather_data = await fetch_all_weather(CITIES)

    await save_to_json(weather_data, "Weather_train.json")
    cleaned_data = clean_weather_data(weather_data)
    await save_to_json(cleaned_data, "weather_cleaned.json")
    logger.info("Weather data processing completed.")


if __name__ == "__main__":
    asyncio.run(main())
