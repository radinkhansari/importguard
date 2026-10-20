from fastapi import FastAPI, UploadFile, HTTPException
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

    errors = []

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

    return {
        "filename": file.filename,
        "row_count": len(rows),
        "rows": rows,
        "errors": errors,
    }