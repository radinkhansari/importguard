import csv
import io

from email_validator import EmailNotValidError, validate_email


def validate_csv(contents: bytes):
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("The file must be UTF-8 encoded text.")

    reader = csv.DictReader(io.StringIO(text), strict=True)

    try:
        headers = reader.fieldnames or []
    except csv.Error:
        raise ValueError(
            "Malformed CSV. Check quotation marks and separators."
        )

    if any(not header.strip() for header in headers):
        raise ValueError("Column names cannot be blank.")

    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate column names are not allowed")

    required_columns = {"name", "email"}
    actual_columns = set(headers)
    missing_columns = required_columns - actual_columns

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    try:
        rows = list(reader)
    except csv.Error:
        raise ValueError(
            "Malformed CSV. Check quotation marks and separators."
        )

    if not rows:
        raise ValueError("The CSV must contain at least one data record.")

    errors = []
    seen_emails = {}

    for record_number, row in enumerate(rows, start=1):
        if None in row:
            errors.append({
                "record": record_number,
                "field": None,
                "message": "Record has more values than the header.",
            })

        for column in ("name", "email"):
            value = row.get(column)

            if value is None or not value.strip():
                errors.append({
                    "record": record_number,
                    "field": column,
                    "message": f"{column} is required.",
                })
            elif column == "email":
                try:
                    email_info = validate_email(
                        value.strip(),
                        check_deliverability=False,
                    )
                except EmailNotValidError as exc:
                    errors.append({
                        "record": record_number,
                        "field": "email",
                        "message": str(exc),
                    })
                else:
                    email = email_info.normalized

                    if email in seen_emails:
                        errors.append({
                            "record": record_number,
                            "field": "email",
                            "message": (
                                f"Email duplicates record {seen_emails[email]}."
                            ),
                        })
                    else:
                        seen_emails[email] = record_number

    invalid_records = {error["record"] for error in errors}
    invalid_count = len(invalid_records)
    valid_count = len(rows) - invalid_count

    return {
        "row_count": len(rows),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "rows": rows,
        "errors": errors,
    }