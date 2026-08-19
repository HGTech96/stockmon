import uvicorn
from fastapi import FastAPI

app = FastAPI(title="stockmon")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("stockmon.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
