from app.validation import validate_csv
import pytest

def test_valid_csv():
    contents = (
        b"name,email\n"
        b"Alice,alice@example.com\n"
        b"Bob,bob@example.com\n"
    )

    result = validate_csv(contents)

    assert result["row_count"] == 2
    assert result["valid_count"] == 2
    assert result["invalid_count"] == 0
    assert result["errors"] == []
    assert result["rows"] == [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]

def test_missing_email_column():
    contents = b"name\nAlice\n"

    with pytest.raises(ValueError, match="Missing required columns: email"):
        validate_csv(contents)


def test_multiple_errors_in_one_record():
    contents = (
        b"name,email\n"
        b",\n"
        b"Bob,bob@example.com\n"
    )

    result = validate_csv(contents)

    assert result["row_count"] == 2
    assert result["valid_count"] == 1
    assert result["invalid_count"] == 1
    assert result["errors"] == [
        {
            "record": 1,
            "field": "name",
            "message": "name is required.",
        },
        {
            "record": 1,
            "field": "email",
            "message": "email is required.",
        },
    ]

def test_duplicate_email():
    contents = (
        b"name,email\n"
        b"Alice,alice@example.com\n"
        b"Bob,bob@example.com\n"
        b"Alice Again,alice@example.com\n"
    )

    result = validate_csv(contents)

    assert result["row_count"] == 3
    assert result["valid_count"] == 2
    assert result["invalid_count"] == 1
    assert result["errors"] == [
        {
            "record": 3,
            "field": "email",
            "message": "Email duplicates record 1.",
        }
    ]