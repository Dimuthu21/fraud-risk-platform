from fastapi import FastAPI

from db import test_connection

app = FastAPI(title="Fraud Risk Platform API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    result = test_connection()

    return {
        "db_connected": True,
        "result": result[0]
    }