import os
import json
import openai
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("POSTGRES_DB_URL")

# Load the merged JSON file once at the top
logger.info("Merged data Opening successfully.")
with open("/home/gokul/work/LLM/Ingestion/Data_json/merged_data.json", "r") as f:
    logger.info("Merged data loaded successfully.")
    merged_data = json.load(f)

# Basic city extractor (can be replaced with NLP if needed)
def extract_city_from_query(query):
    logger.info("Extracting city from query: %s", query)
    known_cities = [entry["city"].lower() for entry in merged_data["weather"]]
    for city in known_cities:
        logger.debug("Checking city: %s", city)
        if city in query.lower():
            logger.info("City found: %s", city)
            return city.title()
    return None

def generate_summary_from_data(user_query):
    # Step 1: Extract city
    logger.info("Generating summary from user query.")
    city = extract_city_from_query(user_query)
    if not city:
        logger.warning("City not found in user query.")
        logger.info("Received query: %s", user_query)
        return "[-] Could not determine city from the query."

    # Step 2: Look up weather data
    logger.info("Looking up weather data for city: %s", city)
    weather_data = merged_data.get("weather", [])
    city_weather = next(
        (entry for entry in weather_data if entry["city"].strip().lower() == city.strip().lower()),
        None
    )

    if not city_weather:
        logger.warning("Weather data for city '%s' not found.", city)
        available_cities = [entry['city'] for entry in weather_data]
        return (
            f"[-] Weather data for '{city}' not found.\n"
            f"[+] Available cities: {available_cities}"
        )
    logger.error("Weather data for city '%s' not found.", city)

    # Step 3: Prepare OpenAI prompt
    wine_list = [wine for entry in merged_data["wine"] for wine in entry]
    prompt = (
        f"The current temperature in {city} is {city_weather['temp_c']}\u00b0C "
        f"and it feels like {city_weather['feels_like_c']}\u00b0C.\n"
        f"From the following wines: {', '.join(wine_list)}, "
        f"choose the most suitable one for this weather.\n"
        f"In your response, explicitly mention the temperature values and explain why the wine is suitable."
    )

    try:
        # Connect to DB first to check for duplicates
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT summary FROM analysis_summaries
            WHERE city = %s AND temperature_c = %s AND feels_like_c = %s
            ORDER BY created_at DESC LIMIT 1;
            """,
            (city, city_weather['temp_c'], city_weather['feels_like_c'])
        )
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            logger.info("Duplicate entry found for city '%s', skipping OpenAI call.", city)
            return "[-] Entry already exists with the same weather data. Not storing again."

        # Call OpenAI
        logger.info("Calling OpenAI API for wine recommendation...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        logger.info("OpenAI API response received. Summary: %s")
        summary = response['choices'][0]['message']['content']

        # Insert into DB
        logger.info("Inserting summary into database...")
        cursor = conn.cursor()
        logger.info("Inserting summary into database for city '%s'.", city)
        cursor.execute(
            """
            INSERT INTO analysis_summaries (city, temperature_c, feels_like_c, wine_recommendation, summary, created_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            [
                city,
                city_weather['temp_c'],
                city_weather['feels_like_c'],
                "TBD",  # optionally parse wine from LLM response
                summary,
                datetime.utcnow()
            ]
        )
        conn.commit()
        logger.info("Summary inserted into database successfully.")
        cursor.close()
        conn.close()
        logger.info("Summary stored in database for city '%s'.", city)

        return summary

    except Exception as e:
        logger.exception("Unexpected error occurred")
        logger.info("Unexpected error occurred")
        return f"[-] Error calling OpenAI or storing to DB: {e}"


# Example usage
if __name__ == "__main__":
    logger.info("Starting the script...")
    logger.info("Loading merged data...")
    query = input("Ask: ")
    response = generate_summary_from_data(query)
    logger.info("Response: %s", response)
    print(response)