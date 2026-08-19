from fastapi import FastAPI

app = FastAPI(title="stockmon")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
