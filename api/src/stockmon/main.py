import uvicorn
from fastapi import FastAPI

from stockmon.api.routes import refresh

app = FastAPI(title="stockmon")
app.include_router(refresh.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("stockmon.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
