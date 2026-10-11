from fastapi import FastAPI

app = FastAPI(title = "ImportGuard")
@app.get("/health")
def health():
    return {"status" : "ok"}