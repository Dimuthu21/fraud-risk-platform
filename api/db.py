import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

connection_url = URL.create(
    "mssql+pyodbc",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_SERVER,
    port=1433,
    database=DB_NAME,
    query={
        "driver": "ODBC Driver 17 for SQL Server",
        "Encrypt": "yes",
        "TrustServerCertificate": "no",
    },
)

engine = create_engine(connection_url)


def test_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS test"))
        return result.fetchone()


def insert_prediction(
    payload_json: str,
    fraud_probability: float,
    risk_level: str,
    decision: str,
    model_version: str,
):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO predictions
                (
                    request_payload,
                    fraud_probability,
                    risk_level,
                    decision,
                    model_version
                )
                VALUES
                (
                    :payload,
                    :prob,
                    :risk,
                    :decision,
                    :version
                )
            """),
            {
                "payload": payload_json,
                "prob": fraud_probability,
                "risk": risk_level,
                "decision": decision,
                "version": model_version,
            },
        )

        conn.commit()