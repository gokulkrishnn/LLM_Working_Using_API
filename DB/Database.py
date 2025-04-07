import psycopg2  # type: ignore
import json
import os
from dotenv import load_dotenv  # type: ignore
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
# Load the database URL from the .env file
logger.info("Loading environment variables...")
DB_URL = os.getenv("POSTGRES_DB_URL")

# Define the path to the merged data file
logger.info("Setting path for merged data...")
MERGED_DATA_PATH = Path(r"E:\NexgenAI\work\src\Ingestion\Data_json\merged_data.json")


def store_json_to_postgres(json_file=MERGED_DATA_PATH):
    # Your PostgreSQL connection string
    logger.info("Connecting to PostgreSQL...")
    connection_string = DB_URL
    logger.info("Connection string loaded.")
    logger.info("Reading JSON file...")

    # Read merged JSON file
    with open(json_file, "r") as f:
        data = json.load(f)
        logger.info("JSON file read successfully.")

    try:
        logger.info("Connecting to PostgreSQL database...")
        # Connect to PostgreSQL using connection string
        conn = psycopg2.connect(connection_string)
        logger.info("Connected to PostgreSQL database.")
        cursor = conn.cursor()
        logger.info("Creating table if not exists...")

        # Ensure table exists
        logger.info("Creating table 'merged_data' if it does not exist...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS merged_data (
                id SERIAL PRIMARY KEY,
                data JSONB
            );
        """)
        logger.info("Table 'merged_data' is ready.")

        # Insert JSON into the table
        logger.info("Inserting JSON data into 'merged_data' table...")
        cursor.execute("INSERT INTO merged_data (data) VALUES (%s);", [json.dumps(data)])
        logger.info("JSON data inserted successfully.")
        conn.commit()
        logger.info("Transaction committed.")
        cursor.close()
        logger.info("Cursor closed.")
        conn.close()
        logger.info("Database connection closed.")

        print("✅ Merged JSON successfully inserted into PostgreSQL.")
        logger.info("Merged JSON successfully inserted into PostgreSQL.")
    except Exception as e:
        logger.error("Failed to insert JSON into PostgreSQL: %s", e)
        print(f"❌ Failed to insert into PostgreSQL: {e}")
        logger.exception("Exception occurred while inserting JSON into PostgreSQL.")


# Call the function with the correct path
if __name__ == "__main__":
    logger.info("Starting the JSON to PostgreSQL insertion process...")
    store_json_to_postgres()