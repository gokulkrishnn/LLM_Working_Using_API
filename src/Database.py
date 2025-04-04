import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()
# Load the database URL from the .env file
DB_URL = os.getenv("POSTGRES_DB_URL")

def store_json_to_postgres(json_file="merged_data.json"):
    # Your PostgreSQL connection string
    connection_string = DB_URL
    
    # Read merged JSON file
    with open(json_file, "r") as f:
        data = json.load(f)

    try:
        # Connect to PostgreSQL using connection string
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS merged_data (
                id SERIAL PRIMARY KEY,
                data JSONB
            );
        """)

        # Insert JSON into the table
        cursor.execute("INSERT INTO merged_data (data) VALUES (%s);", [json.dumps(data)])

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Merged JSON successfully inserted into PostgreSQL.")
    except Exception as e:
        print(f"❌ Failed to insert into PostgreSQL: {e}")

store_json_to_postgres("merged_data.json")

