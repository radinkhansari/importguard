from fastapi import FastAPI, HTTPException, UploadFile

from app.validation import validate_csv


app = FastAPI(title="ImportGuard")


@app.get("/health")
def health():
    return {"status": "ok"}


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
        result = validate_csv(contents)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "filename": file.filename,
        **result,
    }