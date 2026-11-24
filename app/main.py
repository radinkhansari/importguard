from fastapi import FastAPI, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.validation import validate_csv
from app.models import ImportBatch, ImportRecord


app = FastAPI(title="ImportGuard")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/imports")
def upload_csv(file: UploadFile, db: Session = Depends(get_db)):
    max_bytes = 1024 * 1024
    contents = file.file.read(max_bytes + 1)

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 1 MiB size limit.",
        )

    try:
        result = validate_csv(contents)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    errors_by_record = {}
    for error in result["errors"]:
        errors_by_record.setdefault(error["record"], []).append(error)

    with db.begin():
        batch = ImportBatch(filename=file.filename)
        db.add(batch)
        db.flush()

        import_id = batch.id

        for record_number, row in enumerate(result["rows"], start=1):
            record = ImportRecord(
                import_id=import_id,
                record_number=record_number,
                data=row,
                errors=errors_by_record.get(record_number, []),
            )
            db.add(record)

    return {"import_id": import_id, "filename": file.filename, **result}