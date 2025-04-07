from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm import generate_summary_from_data
from typing import Optional
import uvicorn
import psycopg2
from os import getenv
from dotenv import load_dotenv
import logging


# Configure the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

logger.info("Starting FastAPI application...")
logger.info("Loading environment variables...")
logger.info("Getting the post request using the json schema...")
@app.post("/fetch_and_process")
async def fetch_and_process(request: QueryRequest):
    """
    Accepts a question like: "What is the weather in Paris and what wine suits it?"
    Calls LLM logic and stores summary if not duplicate.
    """
    logger.info("/fetch_and_process endpoint called with question: %s", request.question)
    try:
        result = generate_summary_from_data(request.question)
        return {"response": result}
    except Exception as e:
        logger.exception("Unexpected error in /fetch_and_process")
        logger.info("Error details: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


logger.info("Creating /results endpoint...")
@app.get("/results")
async def get_results(city: Optional[str] = None):
    """
    Returns stored weather + wine records (optionally filtered by city).
    """
    logger.info("/results endpoint called%s", f" with city: {city}" if city else "")
    logger.info("Connecting to PostgreSQL database...")
    logger.info("Loading environment variables...")
    logger.info("Loading database URL...")
    load_dotenv()
    conn = psycopg2.connect(getenv("POSTGRES_DB_URL"))
    logger.info("Database URL loaded.")
    logger.info("Connecting to database...")
    cursor = conn.cursor()

    if city:
        logger.info("Filtering results by city: %s", city)
        cursor.execute("SELECT * FROM analysis_summaries WHERE city = %s ORDER BY created_at DESC", (city,))
    else:
        logger.info("Fetching all results.")
        cursor.execute("SELECT * FROM analysis_summaries ORDER BY created_at DESC")

    rows = cursor.fetchall()
    logger.info("Fetched %d rows from the database.", len(rows))
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    logger.info("Processed results into dictionary format.")
    results = [dict(zip(columns, row)) for row in rows]
    return {"data": results}

logger.info("Creating /analysis endpoint...")
@app.get("/analysis")
async def get_latest_summary(city: Optional[str] = None):
    """
    Returns latest LLM-generated summary (optionally for a specific city).

    """
    logger.info("/analysis endpoint called%s", f" with city: {city}" if city else "")
    logger.info("Connecting to PostgreSQL database...")
    logger.info("Loading environment variables...")
    load_dotenv()
    conn = psycopg2.connect(getenv("POSTGRES_DB_URL"))
    cursor = conn.cursor()
    logger.info("Database URL loaded.")
    logger.info("Connecting to database...")

    if city:
        logger.info("Filtering summary by city: %s", city)
        cursor.execute("SELECT summary FROM analysis_summaries WHERE city = %s ORDER BY created_at DESC LIMIT 1", (city,))
    else:
        logger.info("Fetching latest summary without city filter.")
        cursor.execute("SELECT summary FROM analysis_summaries ORDER BY created_at DESC LIMIT 1")

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.info("Fetched summary from the database.")
    logger.info("Closing database connection...")

    logger.info("Returning summary from /analysis endpoint.")
    logger.info("Summary: %s", result[0])
    return {"summary": result[0] if result else "No summary available."}



if __name__ == "__main__":
    logger.info("Starting FastAPI application...")
    logger.info("Loading environment variables...")
    logger.info("Loading database URL...")
    logger.info("Starting server...")
    logger.info("Server started at http://localhost:8080")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)