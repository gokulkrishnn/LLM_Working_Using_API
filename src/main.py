from fastapi import FastAPI, Request
from pydantic import BaseModel
from llm import generate_summary_from_data
from typing import Optional
import uvicorn
import psycopg2
from os import getenv
from dotenv import load_dotenv

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/fetch_and_process")
async def fetch_and_process(request: QueryRequest):
    """
    Accepts a question like: "What is the weather in Paris and what wine suits it?"
    Calls LLM logic and stores summary if not duplicate.
    """
    result = generate_summary_from_data(request.question)
    return {"response": result}

@app.get("/results")
async def get_results(city: Optional[str] = None):
    """
    Returns stored weather + wine records (optionally filtered by city).
    """

    load_dotenv()
    conn = psycopg2.connect(getenv("POSTGRES_DB_URL"))
    cursor = conn.cursor()

    if city:
        cursor.execute("SELECT * FROM analysis_summaries WHERE city = %s ORDER BY created_at DESC", (city,))
    else:
        cursor.execute("SELECT * FROM analysis_summaries ORDER BY created_at DESC")

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    results = [dict(zip(columns, row)) for row in rows]
    return {"data": results}

@app.get("/analysis")
async def get_latest_summary(city: Optional[str] = None):
    """
    Returns latest LLM-generated summary (optionally for a specific city).
    """

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

    return {"summary": result[0] if result else "No summary available."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
