from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_valid_csv():
    contents = b"name,email\nAlice,alice@example.com\n"

    response = client.post(
        "/imports",
        files={"file": ("sample.csv", contents, "text/csv")},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "sample.csv"
    assert data["row_count"] == 1
    assert data["valid_count"] == 1
    assert data["invalid_count"] == 0
    assert data["errors"] == []
    assert data["rows"] == [
        {"name": "Alice", "email": "alice@example.com"}
    ]

def test_upload_missing_email_column():
    contents = b"name\nAlice\n"

    response = client.post(
        "/imports",
        files={"file": ("missing-email.csv", contents, "text/csv")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Missing required columns: email"
    }

def test_upload_too_large():
    contents = b"a" * (1024 * 1024 + 1)

    response = client.post(
        "/imports",
        files={"file": ("too-large.csv", contents, "text/csv")},
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "File exceeds the 1 MiB size limit."
    }