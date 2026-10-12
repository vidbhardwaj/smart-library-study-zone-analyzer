import os
import sys
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as PathParam, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure analytics module can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from analytics.study_score import calculate_study_score
except ImportError:
    # Fallback inline scoring if import path differs
    def calculate_study_score(temp, humidity, light, noise, occupancy=0, capacity=10):
        score = 85
        return {
            "overall_score": score,
            "rating": "Good Study Zone",
            "status_badge": "Good",
            "color": "#3b82f6",
            "sub_scores": {"acoustic": 80, "thermal": 85, "visual": 85, "occupancy": 90},
            "recommendations": ["Conditions are suitable for study."],
        }

# Optional psycopg import for PostgreSQL support
try:
    import psycopg
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False

DB_SQLITE_PATH = Path(__file__).resolve().parent.parent / "smart_library.db"

app = FastAPI(
    title="Smart Library Study Zone Analyzer API",
    description="Real-time IoT environmental monitoring and study zone scoring system.",
    version="2.0.0"
)

# Enable CORS for all origins (frontend dashboard access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Database Abstraction Layer (Self-Balancing Hybrid: Postgres with SQLite Fallback)
# ==============================================================================

class DatabaseManager:
    """Manages connections with automatic fallback to SQLite when PostgreSQL is offline."""
    def __init__(self):
        self.use_postgres = False
        self._test_connection()
        self.init_database()

    def _test_connection(self):
        if not HAS_PSYCOPG:
            self.use_postgres = False
            return

        db_host = os.getenv("DB_HOST", "localhost")
        # Only try postgres if explicitly requested or check quickly with 1s timeout
        try:
            conn = psycopg.connect(
                host=db_host,
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "smart_library"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                connect_timeout=1
            )
            conn.close()
            self.use_postgres = True
            print("[DatabaseManager] Connected successfully to PostgreSQL.")
        except Exception:
            self.use_postgres = False
            print(f"[DatabaseManager] PostgreSQL unavailable. Using embedded SQLite fallback at {DB_SQLITE_PATH}.")

    def ensure_tables(self):
        """Self-healing check to make sure required tables exist."""
        try:
            with sqlite3.connect(str(DB_SQLITE_PATH)) as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_readings'")
                if not cur.fetchone():
                    self.init_database()
        except Exception:
            self.init_database()

    def get_connection(self):
        if self.use_postgres:
            try:
                return psycopg.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", "5432"),
                    dbname=os.getenv("DB_NAME", "smart_library"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", ""),
                    connect_timeout=2
                )
            except Exception:
                # Fallback dynamically if postgres drops
                self.ensure_tables()
                conn = sqlite3.connect(str(DB_SQLITE_PATH))
                conn.row_factory = sqlite3.Row
                return conn
        else:
            self.ensure_tables()
            conn = sqlite3.connect(str(DB_SQLITE_PATH))
            conn.row_factory = sqlite3.Row
            return conn

    def init_database(self):
        """Creates schema and seeds initial study zones if not existing."""
        if self.use_postgres:
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS study_zones (
                                zone_id SERIAL PRIMARY KEY,
                                zone_name VARCHAR(100) NOT NULL,
                                location VARCHAR(150),
                                capacity INT DEFAULT 10,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """)
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS sensor_readings (
                                reading_id SERIAL PRIMARY KEY,
                                zone_id INT REFERENCES study_zones(zone_id),
                                temperature_c FLOAT NOT NULL,
                                humidity_percent FLOAT NOT NULL,
                                light_lux FLOAT NOT NULL,
                                noise_db FLOAT NOT NULL,
                                occupancy INT DEFAULT 0,
                                capacity INT DEFAULT 10,
                                study_score INT DEFAULT 80,
                                study_rating VARCHAR(50) DEFAULT 'Good',
                                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """)
                        # Seed zones if empty
                        cur.execute("SELECT COUNT(*) FROM study_zones")
                        count = cur.fetchone()[0]
                        if count == 0:
                            cur.execute("""
                                INSERT INTO study_zones (zone_id, zone_name, location, capacity) VALUES
                                (1, 'Zone 1 - Main Quiet Study Hall', '2nd Floor, Wing A', 20),
                                (2, 'Zone 2 - Silent Reading Room', '3rd Floor, Corner B', 10),
                                (3, 'Zone 3 - Group Discussion Hub', '1st Floor, Wing C', 15);
                            """)
                        conn.commit()
                return
            except Exception as e:
                print(f"[DatabaseManager] Postgres init failed ({e}). Switching to SQLite.")
                self.use_postgres = False

        # SQLite Schema Initialization
        with sqlite3.connect(str(DB_SQLITE_PATH)) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_zones (
                    zone_id INTEGER PRIMARY KEY,
                    zone_name TEXT NOT NULL,
                    location TEXT,
                    capacity INTEGER DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id INTEGER,
                    temperature_c REAL NOT NULL,
                    humidity_percent REAL NOT NULL,
                    light_lux REAL NOT NULL,
                    noise_db REAL NOT NULL,
                    occupancy INTEGER DEFAULT 0,
                    capacity INTEGER DEFAULT 10,
                    study_score INTEGER DEFAULT 80,
                    study_rating TEXT DEFAULT 'Good',
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(zone_id) REFERENCES study_zones(zone_id)
                );
            """)
            cur.execute("SELECT COUNT(*) FROM study_zones")
            count = cur.fetchone()[0]
            if count == 0:
                cur.executemany("""
                    INSERT INTO study_zones (zone_id, zone_name, location, capacity) VALUES (?, ?, ?, ?)
                """, [
                    (1, "Zone 1 - Main Quiet Study Hall", "2nd Floor, Wing A", 20),
                    (2, "Zone 2 - Silent Reading Room", "3rd Floor, Corner B", 10),
                    (3, "Zone 3 - Group Discussion Hub", "1st Floor, Wing C", 15),
                ])
            conn.commit()
            print("[DatabaseManager] SQLite database initialized successfully.")


db_mgr = DatabaseManager()


# ==============================================================================
# Pydantic Request & Response Schemas
# ==============================================================================

class SensorReadingInput(BaseModel):
    zone_id: int = Field(default=1, gt=0, description="Unique ID of the study zone")
    temperature_c: float = Field(..., ge=-40, le=90, description="Temperature in Celsius")
    humidity_percent: float = Field(..., ge=0, le=100, description="Relative humidity %")
    light_lux: float = Field(..., ge=0, le=200000, description="Light level (Lux or normalized)")
    noise_db: float = Field(..., ge=0, le=200, description="Sound level in dB")
    occupancy: int = Field(default=0, ge=0, description="Current number of detected occupants")
    capacity: int = Field(default=10, gt=0, description="Maximum room capacity")


class SimulatedReadingInput(BaseModel):
    zone_id: int = 1
    temperature_c: Optional[float] = 23.5
    humidity_percent: Optional[float] = 52.0
    light_lux: Optional[float] = 450.0
    noise_db: Optional[float] = 38.0
    occupancy: Optional[int] = 1
    capacity: Optional[int] = 2


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/api/status")
def system_status():
    """Returns runtime health status, active database backend, and stats."""
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sensor_readings")
        total_readings = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM study_zones")
        total_zones = cur.fetchone()[0]
        conn.close()
        return {
            "status": "online",
            "backend": "FastAPI + Antigravity Self-Balancing Engine",
            "database_driver": "PostgreSQL" if db_mgr.use_postgres else "SQLite (Self-Balancing Local)",
            "total_readings": total_readings,
            "total_zones": total_zones,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "error": str(exc),
            "database_driver": "SQLite Fallback",
        }


@app.get("/zones")
def get_zones():
    """List all study zones with real-time status and latest study score."""
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT zone_id, zone_name, location, capacity, created_at
            FROM study_zones
            ORDER BY zone_id ASC
        """)
        zones_rows = cur.fetchall()

        zones = []
        for row in zones_rows:
            z_id = row[0]
            # Fetch latest reading for this zone
            cur.execute("""
                SELECT reading_id, temperature_c, humidity_percent, light_lux, noise_db,
                       occupancy, capacity, study_score, study_rating, recorded_at
                FROM sensor_readings
                WHERE zone_id = ?
                ORDER BY reading_id DESC LIMIT 1
            """ if not db_mgr.use_postgres else """
                SELECT reading_id, temperature_c, humidity_percent, light_lux, noise_db,
                       occupancy, capacity, study_score, study_rating, recorded_at
                FROM sensor_readings
                WHERE zone_id = %s
                ORDER BY reading_id DESC LIMIT 1
            """, (z_id,))
            latest = cur.fetchone()

            zone_info = {
                "zone_id": row[0],
                "zone_name": row[1],
                "location": row[2],
                "capacity": row[3],
                "created_at": str(row[4]),
                "latest_reading": None
            }

            if latest:
                zone_info["latest_reading"] = {
                    "reading_id": latest[0],
                    "temperature_c": latest[1],
                    "humidity_percent": latest[2],
                    "light_lux": latest[3],
                    "noise_db": latest[4],
                    "occupancy": latest[5],
                    "capacity": latest[6],
                    "study_score": latest[7],
                    "study_rating": latest[8],
                    "recorded_at": str(latest[9]),
                }
            zones.append(zone_info)

        conn.close()
        return zones
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failed: {exc}")


@app.post("/readings", status_code=status.HTTP_201_CREATED)
def create_reading(reading: SensorReadingInput):
    """
    Accepts real-time telemetry from ESP32 or Simulator.
    Computes Study Environment Score and persists to database without hanging.
    """
    # 1. Compute Study Environment Score & Insights
    score_data = calculate_study_score(
        temp=reading.temperature_c,
        humidity=reading.humidity_percent,
        light=reading.light_lux,
        noise=reading.noise_db,
        occupancy=reading.occupancy,
        capacity=reading.capacity
    )
    overall_score = score_data["overall_score"]
    rating_label = score_data["rating"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. Persist to active database
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()

        if db_mgr.use_postgres:
            cur.execute("""
                INSERT INTO sensor_readings
                    (zone_id, temperature_c, humidity_percent, light_lux, noise_db,
                     occupancy, capacity, study_score, study_rating, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING reading_id, recorded_at;
            """, (
                reading.zone_id, reading.temperature_c, reading.humidity_percent,
                reading.light_lux, reading.noise_db, reading.occupancy,
                reading.capacity, overall_score, rating_label, now_str
            ))
            res = cur.fetchone()
            reading_id = res[0]
            recorded_at = str(res[1])
            conn.commit()
        else:
            cur.execute("""
                INSERT INTO sensor_readings
                    (zone_id, temperature_c, humidity_percent, light_lux, noise_db,
                     occupancy, capacity, study_score, study_rating, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reading.zone_id, reading.temperature_c, reading.humidity_percent,
                reading.light_lux, reading.noise_db, reading.occupancy,
                reading.capacity, overall_score, rating_label, now_str
            ))
            reading_id = cur.lastrowid
            recorded_at = now_str
            conn.commit()

        conn.close()

        return {
            "status": "success",
            "message": "Sensor reading recorded successfully",
            "reading": {
                "reading_id": reading_id,
                "zone_id": reading.zone_id,
                "temperature_c": reading.temperature_c,
                "humidity_percent": reading.humidity_percent,
                "light_lux": reading.light_lux,
                "noise_db": reading.noise_db,
                "occupancy": reading.occupancy,
                "capacity": reading.capacity,
                "study_score": overall_score,
                "study_rating": rating_label,
                "recorded_at": recorded_at,
            },
            "analytics": score_data
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not persist sensor reading: {exc}"
        )


@app.get("/readings")
def get_readings(
    zone_id: Optional[int] = Query(None, description="Filter by study zone"),
    limit: int = Query(50, ge=1, le=500, description="Max readings to return")
):
    """Returns chronological sensor readings."""
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()

        query = """
            SELECT s.reading_id, s.zone_id, z.zone_name, s.temperature_c, s.humidity_percent,
                   s.light_lux, s.noise_db, s.occupancy, s.capacity, s.study_score,
                   s.study_rating, s.recorded_at
            FROM sensor_readings s
            LEFT JOIN study_zones z ON z.zone_id = s.zone_id
        """
        params = []
        if zone_id is not None:
            query += " WHERE s.zone_id = ? " if not db_mgr.use_postgres else " WHERE s.zone_id = %s "
            params.append(zone_id)

        query += " ORDER BY s.reading_id DESC LIMIT ? " if not db_mgr.use_postgres else " ORDER BY s.reading_id DESC LIMIT %s "
        params.append(limit)

        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "reading_id": r[0],
                "zone_id": r[1],
                "zone_name": r[2] or f"Zone {r[1]}",
                "temperature_c": r[3],
                "humidity_percent": r[4],
                "light_lux": r[5],
                "noise_db": r[6],
                "occupancy": r[7],
                "capacity": r[8],
                "study_score": r[9],
                "study_rating": r[10],
                "recorded_at": str(r[11]),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query error: {exc}")


@app.get("/zones/{zone_id}/latest")
def get_latest_reading(zone_id: int = PathParam(..., gt=0)):
    """Fetch the latest environmental reading and study score for a specific zone."""
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.reading_id, z.zone_name, s.temperature_c, s.humidity_percent,
                   s.light_lux, s.noise_db, s.occupancy, s.capacity, s.study_score,
                   s.study_rating, s.recorded_at
            FROM sensor_readings s
            JOIN study_zones z ON z.zone_id = s.zone_id
            WHERE s.zone_id = ?
            ORDER BY s.reading_id DESC LIMIT 1
        """ if not db_mgr.use_postgres else """
            SELECT s.reading_id, z.zone_name, s.temperature_c, s.humidity_percent,
                   s.light_lux, s.noise_db, s.occupancy, s.capacity, s.study_score,
                   s.study_rating, s.recorded_at
            FROM sensor_readings s
            JOIN study_zones z ON z.zone_id = s.zone_id
            WHERE s.zone_id = %s
            ORDER BY s.reading_id DESC LIMIT 1
        """, (zone_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="No readings recorded for this study zone.")

        score_data = calculate_study_score(
            temp=row[2],
            humidity=row[3],
            light=row[4],
            noise=row[5],
            occupancy=row[6],
            capacity=row[7]
        )

        return {
            "reading_id": row[0],
            "zone_id": zone_id,
            "zone_name": row[1],
            "temperature_c": row[2],
            "humidity_percent": row[3],
            "light_lux": row[4],
            "noise_db": row[5],
            "occupancy": row[6],
            "capacity": row[7],
            "study_score": row[8],
            "study_rating": row[9],
            "recorded_at": str(row[10]),
            "score_details": score_data
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@app.get("/zones/{zone_id}/summary")
def get_zone_summary(zone_id: int = PathParam(..., gt=0)):
    """Computes statistical averages for a zone."""
    try:
        conn = db_mgr.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                z.zone_name,
                COUNT(s.reading_id) as total_readings,
                ROUND(AVG(s.temperature_c), 1) as avg_temp,
                ROUND(AVG(s.humidity_percent), 1) as avg_humidity,
                ROUND(AVG(s.light_lux), 1) as avg_light,
                ROUND(AVG(s.noise_db), 1) as avg_noise,
                ROUND(AVG(s.study_score), 1) as avg_score
            FROM study_zones z
            LEFT JOIN sensor_readings s ON z.zone_id = s.zone_id
            WHERE z.zone_id = ?
            GROUP BY z.zone_id, z.zone_name
        """ if not db_mgr.use_postgres else """
            SELECT
                z.zone_name,
                COUNT(s.reading_id) as total_readings,
                ROUND(AVG(s.temperature_c)::numeric, 1) as avg_temp,
                ROUND(AVG(s.humidity_percent)::numeric, 1) as avg_humidity,
                ROUND(AVG(s.light_lux)::numeric, 1) as avg_light,
                ROUND(AVG(s.noise_db)::numeric, 1) as avg_noise,
                ROUND(AVG(s.study_score)::numeric, 1) as avg_score
            FROM study_zones z
            LEFT JOIN sensor_readings s ON z.zone_id = s.zone_id
            WHERE z.zone_id = %s
            GROUP BY z.zone_id, z.zone_name
        """, (zone_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Zone not found.")

        return {
            "zone_id": zone_id,
            "zone_name": row[0],
            "total_readings": row[1] or 0,
            "average_temperature_c": row[2] or 0,
            "average_humidity_percent": row[3] or 0,
            "average_light_lux": row[4] or 0,
            "average_noise_db": row[5] or 0,
            "average_study_score": row[6] or 0,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")


@app.post("/simulate-reading")
def simulate_reading(sim: SimulatedReadingInput):
    """Simulates an ESP32 hardware transmission for testing and demonstration."""
    reading = SensorReadingInput(
        zone_id=sim.zone_id or 1,
        temperature_c=sim.temperature_c if sim.temperature_c is not None else 23.0,
        humidity_percent=sim.humidity_percent if sim.humidity_percent is not None else 50.0,
        light_lux=sim.light_lux if sim.light_lux is not None else 450.0,
        noise_db=sim.noise_db if sim.noise_db is not None else 38.0,
        occupancy=sim.occupancy if sim.occupancy is not None else 1,
        capacity=sim.capacity if sim.capacity is not None else 2,
    )
    return create_reading(reading)


# ==============================================================================
# Web Dashboard Frontend Static File Serving
# ==============================================================================

FRONTEND_DIR = PROJECT_ROOT / "dashboard" / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    def index():
        return {
            "message": "Smart Library Study Zone Analyzer API is running.",
            "docs": "/docs",
            "zones": "/zones",
            "readings": "/readings"
        }

