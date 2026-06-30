import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_and_social_flow():
    # 1. Login/Register a mock user
    login_response = client.post(
        "/api/auth/login",
        json={"email": "socialtest@example.com", "password": "securepassword123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test single analysis
    single_response = client.post(
        "/api/social/analyze",
        json={"platform": "youtube", "text": "I really love the camera quality of this new phone! Outstanding performance!"},
        headers=headers
    )
    assert single_response.status_code == 200
    single_data = single_response.json()
    assert single_data["platform"] == "youtube"
    assert single_data["sentiment"] in ["positive", "mixed"]
    assert single_data["emotion"] is not None
    record_id = single_data["id"]

    # 3. Test batch analysis
    batch_response = client.post(
        "/api/social/batch",
        json={
            "platform": "twitter",
            "text": "This product is absolutely amazing! Best purchase ever.\nThe battery life is extremely poor and it keeps crashing.\nOh great, my package arrived late. Wonderful service."
        },
        headers=headers
    )
    assert batch_response.status_code == 200
    batch_data = batch_response.json()
    assert batch_data["total_processed"] == 3
    assert "keywords" in batch_data
    assert "insights" in batch_data
    assert len(batch_data["results"]) == 3

    # Check keyword extraction
    kws = batch_data["keywords"]
    assert len(kws["most_frequent"]) > 0

    # Check business insights
    insights = batch_data["insights"]
    assert insights["total_count"] == 3
    assert len(insights["top_praises"]) > 0
    assert len(insights["top_complaints"]) > 0

    # 4. Test history with filtering
    history_response = client.get(
        "/api/social/history",
        params={"platform": "youtube"},
        headers=headers
    )
    assert history_response.status_code == 200
    history_data = history_response.json()
    # At least the single analyze record we added earlier should be here
    assert len(history_data) >= 1
    assert all(item["platform"] == "youtube" for item in history_data)

    # 5. Test history detail
    detail_response = client.get(
        f"/api/social/history/{record_id}",
        headers=headers
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == record_id

    # 6. Test delete record
    delete_response = client.delete(
        f"/api/social/{record_id}",
        headers=headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Social analysis record deleted successfully."

    # Verify detail returns 404 now
    detail_check = client.get(
        f"/api/social/history/{record_id}",
        headers=headers
    )
    assert detail_check.status_code == 404
