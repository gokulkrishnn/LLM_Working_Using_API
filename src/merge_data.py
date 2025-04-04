import json
import asyncio
from pathlib import Path
from aiofiles import open as aio_open  # type: ignore # Async file handling

# Define file paths using pathlib
WEATHER_FILE = Path("Data_Json/Weather_cleaned.json")
WINE_FILE = Path("Data_Json/Wine_train.json")
MERGED_FILE = Path("Data_Json/merged_data.json")


async def load_json_async(file_path: Path):
    """
    Asynchronously loads JSON data from a given file.

    Args:
        file_path (Path): Path to the JSON file.

    Returns:
        dict or list: Parsed JSON data.
    """
    if not file_path.exists():
        print(f"Warning: {file_path} not found. Skipping...")
        return {}

    try:
        async with aio_open(file_path, "r") as f:
            content = await f.read()
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"Error: {file_path} contains invalid JSON data.")
        return {}
    except Exception as e:
        print(f"Unexpected error while reading {file_path}: {e}")
        return {}


async def save_json_async(data, file_path: Path):
    """
    Asynchronously saves JSON data to a file.

    Args:
        data (dict or list): The JSON-serializable data.
        file_path (Path): Path to save the JSON file.
    """
    try:
        async with aio_open(file_path, "w") as f:
            await f.write(json.dumps(data, indent=4))
        print(f"✅ Merged data successfully saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving JSON to {file_path}: {e}")


async def merge_json_files():
    """
    Asynchronously loads and merges JSON data from WEATHER_FILE and WINE_FILE, 
    then saves the combined data to MERGED_FILE.
    """
    # Load both JSON files concurrently
    weather_data, wine_data = await asyncio.gather(
        load_json_async(WEATHER_FILE),
        load_json_async(WINE_FILE)
    )

    # Merge into structured format
    merged_data = {
        "weather": weather_data or [],
        "wine": wine_data or []
    }

    # Save merged data
    await save_json_async(merged_data, MERGED_FILE)


# Run the async merge function
if __name__ == "__main__":
    asyncio.run(merge_json_files())
