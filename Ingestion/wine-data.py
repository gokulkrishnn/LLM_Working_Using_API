import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key from .env file
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Ensure API key is loaded correctly
if not SPOONACULAR_API_KEY:
    logger.error("Missing API key. Make sure SPOONACULAR_API_KEY is set in your .env file.")
    raise ValueError("Missing API key. Make sure SPOONACULAR_API_KEY is set in your .env file.")

# Base URL for Spoonacular Wine API
WINE_API_URL = "https://api.spoonacular.com/food/wine/description"

# Ensure Data_json directory exists
DATA_DIR = "Data_json"
os.makedirs(DATA_DIR, exist_ok=True)

# List of wines to fetch descriptions for
WINES = [
    "merlot", "chardonnay", "malbec", "riesling", "cabernet sauvignon",
    "pinot noir", "sauvignon blanc", "syrah", "zinfandel", "tempranillo", "grenache"
]

async def fetch_wine_description(session, wine_name):
    """
    Fetches the description of a given wine asynchronously with error handling and logging.
    """
    url = f"{WINE_API_URL}?wine={wine_name}&apiKey={SPOONACULAR_API_KEY}"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Successfully fetched description for {wine_name}")
                return {"wine": wine_name, "description": data.get("wineDescription", "No description available")}
            else:
                logger.warning(f"Failed to fetch description for {wine_name}, HTTP Status: {response.status}")
                return {"wine": wine_name, "error": f"HTTP {response.status}: Unable to fetch data"}
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching description for {wine_name}")
        return {"wine": wine_name, "error": "Timeout while fetching data"}
    except aiohttp.ClientError as e:
        logger.error(f"Request failed for {wine_name}: {str(e)}")
        return {"wine": wine_name, "error": f"Request failed: {str(e)}"}

async def fetch_all_wine_descriptions():
    """
    Fetches descriptions for all wines in the list asynchronously.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_wine_description(session, wine) for wine in WINES]
        return await asyncio.gather(*tasks)

async def save_wine_to_json(data, filename="Wine_train.json"):
    """
    Saves the given data to a JSON file inside Data_json directory.
    """
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"Data saved successfully to {file_path}")
    except IOError as e:
        logger.error(f"Failed to save data to {file_path}: {str(e)}")

async def main():
    """
    Main function that fetches wine descriptions and saves them to a JSON file.
    """
    logger.info("Starting wine description fetch...")
    wine_descriptions = await fetch_all_wine_descriptions()
    await save_wine_to_json(wine_descriptions, "Wine_train.json")
    logger.info("Wine descriptions saved successfully.")

if __name__ == "__main__":
    asyncio.run(main())
