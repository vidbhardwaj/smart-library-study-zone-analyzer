
import os
from pydantic import BaseModel, Field
import psycopg
from fastapi import FastAPI, HTTPException, Path

app = FastAPI(title="Smart Library Study Zone Analyzer API")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "smart_library"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


@app.get("/")
def home():
    return {
        "message": "Smart Library API is running",
        "docs": "/docs",
    }


@app.get("/zones")
def get_zones():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT zone_id, zone_name, location, created_at
                FROM study_zones
                ORDER BY zone_id
                """
            ).fetchall()

        return [
            {
                "zone_id": row[0],
                "zone_name": row[1],
                "location": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=500,
            detail="Database query failed. Check database credentials.",
        ) from exc


@app.get("/readings")
def get_readings():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    z.zone_name,
                    s.reading_id,
                    s.temperature_c,
                    s.humidity_percent,
                    s.light_lux,
                    s.noise_db,
                    s.recorded_at
                FROM sensor_readings s
                JOIN study_zones z ON z.zone_id = s.zone_id
                ORDER BY s.recorded_at DESC, s.reading_id DESC
                LIMIT 100
                """
            ).fetchall()

        return [
            {
                "zone_name": row[0],
                "reading_id": row[1],
                "temperature_c": row[2],
                "humidity_percent": row[3],
                "light_lux": row[4],
                "noise_db": row[5],
                "recorded_at": row[6],
            }
            for row in rows
        ]
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=500,
            detail="Database query failed. Check database credentials.",
        ) from exc

class SensorReadingInput(BaseModel):
    zone_id: int = Field(gt=0)
    temperature_c: float = Field(ge=-20, le=80)
    humidity_percent: float = Field(ge=0, le=100)
    light_lux: float = Field(ge=0, le=200000)
    noise_db: float = Field(ge=0, le=200)


@app.post("/readings", status_code=201)
def create_reading(reading: SensorReadingInput):
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO sensor_readings
                    (zone_id, temperature_c, humidity_percent,
                     light_lux, noise_db)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reading_id, zone_id, temperature_c,
                          humidity_percent, light_lux, noise_db,
                          recorded_at
                """,
                (
                    reading.zone_id,
                    reading.temperature_c,
                    reading.humidity_percent,
                    reading.light_lux,
                    reading.noise_db,
                ),
            ).fetchone()

        return {
            "message": "Sensor reading saved successfully",
            "reading": {
                "reading_id": row[0],
                "zone_id": row[1],
                "temperature_c": row[2],
                "humidity_percent": row[3],
                "light_lux": row[4],
                "noise_db": row[5],
                "recorded_at": row[6],
            },
        }
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(
            status_code=404,
            detail="Study zone not found",
        ) from exc
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not save sensor reading",
        ) from exc

@app.get("/zones/{zone_id}/latest")
def get_latest_reading(zone_id: int = Path(gt=0)):
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    z.zone_name,
                    s.temperature_c,
                    s.humidity_percent,
                    s.light_lux,
                    s.noise_db,
                    s.recorded_at
                FROM study_zones z
                JOIN sensor_readings s ON z.zone_id = s.zone_id
                WHERE z.zone_id = %s
                ORDER BY s.recorded_at DESC, s.reading_id DESC
                LIMIT 1
                """,
                (zone_id,),
            ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="No readings found for this study zone",
            )

        return {
            "zone_name": row[0],
            "temperature_c": row[1],
            "humidity_percent": row[2],
            "light_lux": row[3],
            "noise_db": row[4],
            "recorded_at": row[5],
        }
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=500,
            detail="Database query failed",
        ) from exc

@app.get("/zones/{zone_id}/summary")
def get_zone_summary(zone_id: int = Path(gt=0)):
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    z.zone_name,
                    COUNT(s.reading_id),
                    AVG(s.temperature_c),
                    AVG(s.humidity_percent),
                    AVG(s.light_lux),
                    AVG(s.noise_db)
                FROM study_zones z
                LEFT JOIN sensor_readings s
                    ON z.zone_id = s.zone_id
                WHERE z.zone_id = %s
                GROUP BY z.zone_id, z.zone_name
                """,
                (zone_id,),
            ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Study zone not found",
            )

        return {
            "zone_name": row[0],
            "total_readings": row[1],
            "average_temperature_c": row[2],
            "average_humidity_percent": row[3],
            "average_light_lux": row[4],
            "average_noise_db": row[5],
        }
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=500,
            detail="Database query failed",
        ) from exc
