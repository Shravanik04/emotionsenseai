import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_text():
    response = client.post(
        "/api/analyze-text",
        json={"text": "I absolutely love this product, it works wonders!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] == "positive"
    assert data["confidence"] > 0.5

def test_analyze_batch():
    # Create a fake csv file
    csv_content = "review\nThis is great\nThis is terrible\n"
    response = client.post(
        "/api/analyze-batch",
        files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["processed_rows"] == 2
