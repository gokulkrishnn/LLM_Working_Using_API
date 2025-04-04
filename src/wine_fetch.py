import aiohttp  # type: ignore
import asyncio
import os
from dotenv import load_dotenv
import json

# Load API key from .env file
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Ensure API key is loaded correctly
if not SPOONACULAR_API_KEY:
    raise ValueError("Missing API key. Make sure SPOONACULAR_API_KEY is set in your .env file.")

# Base URL for Spoonacular Wine API
WINE_API_URL = "https://api.spoonacular.com/food/wine/description"


# List of wines to fetch descriptions for
WINES = [
    "merlot",
    "chardonnay",
    "malbec",
    "riesling",
    "cabernet sauvignon",
    "pinot noir",
    "sauvignon blanc",
    "syrah",
    "zinfandel",
    "tempranillo",
    "grenache"
]


async def fetch_wine_description(session, wine_name):
    """
    Fetches the description of a given wine asynchronously.
    
    Args:
        session (aiohttp.ClientSession): The session object for making HTTP requests.
        wine_name (str): The name of the wine to fetch the description for.
    
    Returns:
        dict: A dictionary containing the wine name and its description or an error message.
    """
    url = f"{WINE_API_URL}?wine={wine_name}&apiKey={SPOONACULAR_API_KEY}"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return {wine_name: data.get("wineDescription", "No description available")}
            else:
                return {wine_name: f"Error: {response.status}"}
    except asyncio.TimeoutError:
        return {wine_name: "Timeout while fetching data"}
    except aiohttp.ClientError as e:
        return {wine_name: f"Request failed: {str(e)}"}


async def fetch_all_wine_descriptions():
    """
    Fetches descriptions for all wines in the list asynchronously.
    
    Returns:
        list: A list of dictionaries containing wine descriptions.
    """
    async with aiohttp.ClientSession() as session:
        # Create tasks for each wine description request
        tasks = [fetch_wine_description(session, wine) for wine in WINES]
        return await asyncio.gather(*tasks)  # Gather all tasks asynchronously


async def save_wine_to_json(data, filename="Wine_train.json"):
    """
    Saves the given data to a JSON file.
    
    Args:
        data (list): List of wine descriptions.
        filename (str, optional): The filename to save the JSON data. Defaults to "Wine_train.json".
    """
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)


async def main():
    """
    Main function that fetches wine descriptions and saves them to a JSON file.
    """
    wine_descriptions = await fetch_all_wine_descriptions()  # Fetch all wine descriptions
    await save_wine_to_json(wine_descriptions, "Wine_train.json")  # Save data to JSON file
    print("Wine descriptions saved to Wine_train.json")  # Print confirmation message


# Run the script only if executed directly
if __name__ == "__main__":
    asyncio.run(main())
