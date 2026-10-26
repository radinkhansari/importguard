from fastapi import FastAPI, UploadFile, HTTPException
from email_validator import validate_email, EmailNotValidError
import csv
import io

app = FastAPI(title = "ImportGuard")

@app.get("/health")
def health():
    return {"status" : "ok"}

@app.post("/imports")
def upload_csv(file: UploadFile):
    max_bytes = 1024 * 1024
    contents = file.file.read(max_bytes + 1)

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 1 MiB size limit.",
        )
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The file must be UTF-8 encoded text.",
        )
    reader = csv.DictReader(io.StringIO(text), strict = True)

    try:
        headers = reader.fieldnames or []
    except csv.Error:
        raise HTTPException(
        status_code=400,
        detail="Malformed CSV. Check quotation marks and separators.",
    )

    if any(not header.strip() for header in headers):
        raise HTTPException(
            status_code=400,
            detail="Column names cannot be blank.",
        )  
    
    if len(headers) != len(set(headers)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate column names are not allowed"
        )

    required_columns = {"name", "email"}
    actual_columns = set(headers)
    missing_columns = required_columns - actual_columns

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing_columns))}",
    )
    try:
        rows = list(reader)
    except csv.Error:
        raise HTTPException(
        status_code=400,
        detail="Malformed CSV. Check quotation marks and separators.",
    )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="The CSV must contain at least one data record.",
    )
    
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
    "filename": file.filename,
    "row_count": len(rows),
    "valid_count": valid_count,
    "invalid_count": invalid_count,
    "rows": rows,
    "errors": errors,
    }