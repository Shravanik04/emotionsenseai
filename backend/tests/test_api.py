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
    assert data["sentiment_confidence"] > 0.5

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

def test_analyze_batch_custom_column():
    # CSV file with a single custom column named "tweets" (not in original VALID_COLUMNS)
    csv_content = "tweets\nHappy day\nSad day\n"
    response = client.post(
        "/api/analyze-batch",
        files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["processed_rows"] == 2

def test_analyze_batch_single_column_no_header():
    # CSV file with only one column, custom name "something_else"
    csv_content = "something_else\nAwesome experience\nBad quality\n"
    response = client.post(
        "/api/analyze-batch",
        files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["processed_rows"] == 2

def test_analyze_batch_encodings():
    # Test Latin-1 encoding
    csv_content = "review\nRésumé is great\n"
    response = client.post(
        "/api/analyze-batch",
        files={"file": ("test.csv", csv_content.encode("latin1"), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1

def test_analyze_batch_txt():
    # Test plain text file parsing
    txt_content = "Line one\nLine two\nLine three"
    response = client.post(
        "/api/analyze-batch",
        files={"file": ("test.txt", txt_content.encode("utf-8"), "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 3
    assert data["processed_rows"] == 3

def test_excel_parsing_utilities():
    # Test csv_utils directly for Excel file parsing to verify xlrd and openpyxl
    from app.utils.csv_utils import parse_excel
    import pandas as pd
    from io import BytesIO

    # Create a dummy dataframe
    df = pd.DataFrame({"Sentence": ["Excel test 1", "Excel test 2"]})

    # Write to bytes (.xlsx format - openpyxl)
    xlsx_bytes = BytesIO()
    df.to_excel(xlsx_bytes, index=False, engine="openpyxl")
    xlsx_data = xlsx_bytes.getvalue()

    # Parse it
    res_xlsx = parse_excel(xlsx_data, "test.xlsx")
    assert res_xlsx == ["Excel test 1", "Excel test 2"]

