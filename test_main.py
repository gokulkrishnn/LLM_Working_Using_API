from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@patch("main.generate_summary_from_data")
def test_fetch_and_process(mock_llm):
    mock_llm.return_value = "Sunny and 20°C. A nice rosé would suit the weather."
    response = client.post("/fetch_and_process", json={"question": "What is the weather in Paris and what wine suits it?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

@patch("main.psycopg2.connect")
def test_get_results(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (1, "Paris", "Sunny and 20°C. Try a rosé.", "2025-04-01 12:00:00")
    ]
    mock_cursor.description = [("id",), ("city",), ("summary",), ("created_at",)]
    mock_connect.return_value.cursor.return_value = mock_cursor

    response = client.get("/results")
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

@patch("main.psycopg2.connect")
def test_get_results_with_city(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (2, "Paris", "Chilly. A Merlot works well.", "2025-04-02 15:00:00")
    ]
    mock_cursor.description = [("id",), ("city",), ("summary",), ("created_at",)]
    mock_connect.return_value.cursor.return_value = mock_cursor

    response = client.get("/results?city=Paris")
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

@patch("main.psycopg2.connect")
def test_get_analysis(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("Sunny and 20°C. Try a Sauvignon Blanc.",)
    mock_connect.return_value.cursor.return_value = mock_cursor

    response = client.get("/analysis")
    assert response.status_code == 200
    assert "summary" in response.json()
    assert isinstance(response.json()["summary"], str)

@patch("main.psycopg2.connect")
def test_get_analysis_with_city(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("Cloudy. Pinot Noir recommended.",)
    mock_connect.return_value.cursor.return_value = mock_cursor

    response = client.get("/analysis?city=Paris")
    assert response.status_code == 200
    assert "summary" in response.json()
    assert isinstance(response.json()["summary"], str)
