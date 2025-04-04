import os
import json
import openai
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("POSTGRES_DB_URL")

# Load the merged JSON file once at the top
with open("merged_data.json", "r") as f:
    merged_data = json.load(f)

# Basic city extractor (can be replaced with NLP if needed)
def extract_city_from_query(query):
    known_cities = [entry["city"].lower() for entry in merged_data["weather"]]
    for city in known_cities:
        if city in query.lower():
            return city.title()
    return None

def generate_summary_from_data(user_query):
    # Step 1: Extract city
    city = extract_city_from_query(user_query)
    if not city:
        return "[-] Could not determine city from the query."

    # Step 2: Look up weather data
    weather_data = merged_data.get("weather", [])
    city_weather = next(
        (entry for entry in weather_data if entry["city"].strip().lower() == city.strip().lower()),
        None
    )

    if not city_weather:
        available_cities = [entry['city'] for entry in weather_data]
        return (
            f"[-] Weather data for '{city}' not found.\n"
            f"[+] Available cities: {available_cities}"
        )

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
            return "[-] Entry already exists with the same weather data. Not storing again."

        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        summary = response['choices'][0]['message']['content']

        # Insert into DB
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_summaries (city, temperature_c, feels_like_c, wine_recommendation, summary, created_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                city,
                city_weather['temp_c'],
                city_weather['feels_like_c'],
                "TBD",  # optionally parse wine from LLM response
                summary,
                datetime.utcnow()
            )
        )
        conn.commit()
        cursor.close()
        conn.close()

        return summary

    except Exception as e:
        return f"[-] Error calling OpenAI or storing to DB: {e}"


# Example usage
if __name__ == "__main__":
    query = input("Ask: ")
    response = generate_summary_from_data(query)
    print(response)
