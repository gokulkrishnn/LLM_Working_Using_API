from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from models.llm import generate_summary_from_data
from typing import Optional
import uvicorn
import psycopg2
import logging
from os import getenv
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/fetch_and_process")
async def fetch_and_process(request: QueryRequest):
    """
    Accepts a question like: "What is the weather in Paris and what wine suits it?"
    Calls LLM logic and stores summary if not duplicate.
    """
    logger.info("/fetch_and_process endpoint called with question: %s", request.question)
    try:
        result, status = generate_summary_from_data(request.question)
        return result, status
    except Exception as e:
        logger.exception("Unexpected error in /fetch_and_process")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/results")
async def get_results(city: Optional[str] = None):
    """
    Returns stored weather + wine records (optionally filtered by city).
    """
    logger.info("/results endpoint called%s", f" with city: {city}" if city else "")
    try:
        load_dotenv()
        conn = psycopg2.connect(getenv("POSTGRES_DB_URL"))
        cursor = conn.cursor()

        if city:
            cursor.execute("SELECT * FROM analysis_summaries WHERE city = %s ORDER BY created_at DESC", (city,))
        else:
            cursor.execute("SELECT * FROM analysis_summaries ORDER BY created_at DESC")

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

        cursor.close()
        conn.close()

        return {"data": results}

    except psycopg2.Error as db_err:
        logger.exception("Database error in /results")
        raise HTTPException(status_code=500, detail="Database connection failed.")

    except Exception as e:
        logger.exception("Unexpected error in /results")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/analysis")
async def get_latest_summary(city: Optional[str] = None):
    """
    Returns latest LLM-generated summary (optionally for a specific city).
    """
    logger.info("/analysis endpoint called%s", f" with city: {city}" if city else "")
    try:
        load_dotenv()
        conn = psycopg2.connect(getenv("POSTGRES_DB_URL"))
        cursor = conn.cursor()

        if city:
            cursor.execute("SELECT summary FROM analysis_summaries WHERE city = %s ORDER BY created_at DESC LIMIT 1", (city,))
        else:
            cursor.execute("SELECT summary FROM analysis_summaries ORDER BY created_at DESC LIMIT 1")

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            logger.warning("No summary found in /analysis for city: %s", city)
            raise HTTPException(status_code=404, detail="No summary available.")

        return {"summary": result[0]}

    except psycopg2.Error as db_err:
        logger.exception("Database error in /analysis")
        raise HTTPException(status_code=500, detail="Database connection failed.")

    except Exception as e:
        logger.exception("Unexpected error in /analysis")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
