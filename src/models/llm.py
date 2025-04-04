import os
import json
import openai
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("POSTGRES_DB_URL")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load merged data
try:
    with open(r"E:\NexgenAI\work\src\Ingestion\Data_json\merged_data.json", "r") as f:
        merged_data = json.load(f)
    logger.info("Merged data loaded successfully.")
except Exception as e:
    logger.exception("Failed to load merged_data.json")
    raise SystemExit(1)

def extract_city_from_query(query):
    known_cities = [entry["city"].lower() for entry in merged_data.get("weather", [])]
    for city in known_cities:
        if city in query.lower():
            return city.title()
    return None

def generate_summary_from_data(user_query):
    logger.info("Received query: %s", user_query)
    try:
        city = extract_city_from_query(user_query)
        if not city:
            logger.warning("City not found in user query.")
            return {"error": "Could not determine city from the query."}, 400

        weather_data = merged_data.get("weather", [])
        city_weather = next(
            (entry for entry in weather_data if entry["city"].strip().lower() == city.strip().lower()),
            None
        )

        if not city_weather:
            available_cities = [entry['city'] for entry in weather_data]
            logger.warning("Weather data for city '%s' not found.", city)
            return {
                "error": f"Weather data for '{city}' not found.",
                "available_cities": available_cities
            }, 404

        wine_list = [wine for entry in merged_data.get("wine", []) for wine in entry]
        prompt = (
            f"The current temperature in {city} is {city_weather['temp_c']}°C and it feels like {city_weather['feels_like_c']}°C.\n"
            f"From the following wines: {', '.join(wine_list)}, choose the most suitable one for this weather.\n"
            f"In your response, explicitly mention the temperature values and explain why the wine is suitable."
        )

        with psycopg2.connect(DB_URL, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cursor:
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
                    logger.info("Duplicate entry found for city '%s', skipping OpenAI call.", city)
                    return {"message": "Entry already exists. Not storing again."}, 200

        logger.info("Calling OpenAI API for wine recommendation...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        summary = response['choices'][0]['message']['content']

        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO analysis_summaries (city, temperature_c, feels_like_c, wine_recommendation, summary, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        city,
                        city_weather['temp_c'],
                        city_weather['feels_like_c'],
                        "TBD",
                        summary,
                        datetime.utcnow()
                    )
                )
                conn.commit()
                logger.info("Summary stored in database for city '%s'.", city)

        return {"summary": summary}, 201

    except openai.error.OpenAIError as e:
        logger.exception("OpenAI API error")
        return {"error": f"OpenAI API error: {str(e)}"}, 502

    except psycopg2.Error as db_err:
        logger.exception("Database error")
        return {"error": f"Database error: {str(db_err)}"}, 500

    except Exception as e:
        logger.exception("Unexpected error occurred")
        return {"error": f"Internal server error: {str(e)}"}, 500

# Example usage
if __name__ == "__main__":
    query = input("Ask: ")
    response, status = generate_summary_from_data(query)
    print(f"Status: {status}\nResponse: {response}")
