from fastapi import FastAPI, UploadFile, HTTPException
import csv
import io

app = FastAPI(title = "ImportGuard")

@app.get("/health")
def health():
    return {"status" : "ok"}

@app.post("/imports")
def upload_csv(file: UploadFile):
    contents = file.file.read()
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The file must be UTF-8 encoded text.",
        )
    reader = csv.DictReader(io.StringIO(text))

    headers = reader.fieldnames or []
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

    rows = list(reader)
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