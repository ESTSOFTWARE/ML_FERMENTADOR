import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from src.domain.entities.anomaly_inference import AnomalyInference
from src.domain.repositories.inference_repository import InferenceRepository

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS anomaly_inferences (
    inference_id    TEXT PRIMARY KEY,
    session_id      INTEGER,
    circuit_id      INTEGER,
    timestamp       TEXT NOT NULL,
    ph              REAL NOT NULL,
    temperature_c   REAL NOT NULL,
    turbidity       REAL NOT NULL,
    conductivity    REAL NOT NULL,
    alcohol_percent REAL NOT NULL,
    history_length  INTEGER NOT NULL,
    is_anomaly      INTEGER NOT NULL,
    anomaly_score   REAL NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_id ON anomaly_inferences(session_id);
CREATE INDEX IF NOT EXISTS idx_is_anomaly ON anomaly_inferences(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_created_at ON anomaly_inferences(created_at);
"""

INSERT_SQL = """
INSERT INTO anomaly_inferences (
    inference_id, session_id, circuit_id, timestamp,
    ph, temperature_c, turbidity, conductivity, alcohol_percent,
    history_length, is_anomaly, anomaly_score, model_version, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class SqliteInferenceRepository(InferenceRepository):
    """
    Implementación de InferenceRepository usando SQLite local.
    El archivo de BD se crea automáticamente si no existe,
    ideal para entornos sin configuración de red.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(CREATE_TABLE_SQL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, inference: AnomalyInference) -> None:
        with self._connect() as conn:
            conn.execute(INSERT_SQL, (
                str(inference.id),
                inference.session_id,
                inference.circuit_id,
                inference.timestamp.isoformat(),
                inference.ph,
                inference.temperature_c,
                inference.turbidity,
                inference.conductivity,
                inference.alcohol_percent,
                inference.history_length,
                int(inference.is_anomaly),
                inference.anomaly_score,
                inference.model_version,
                inference.created_at.isoformat(),
            ))

    def get_all(self, limit: int = 100) -> list[AnomalyInference]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM anomaly_inferences ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def get_by_session_id(self, session_id: int) -> list[AnomalyInference]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM anomaly_inferences WHERE session_id = ? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def get_anomalies_only(self, limit: int = 100) -> list[AnomalyInference]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM anomaly_inferences WHERE is_anomaly = 1 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_entity(row: sqlite3.Row) -> AnomalyInference:
        return AnomalyInference(
            id=UUID(row["inference_id"]),
            session_id=row["session_id"],
            circuit_id=row["circuit_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            ph=row["ph"],
            temperature_c=row["temperature_c"],
            turbidity=row["turbidity"],
            conductivity=row["conductivity"],
            alcohol_percent=row["alcohol_percent"],
            history_length=row["history_length"],
            is_anomaly=bool(row["is_anomaly"]),
            anomaly_score=row["anomaly_score"],
            model_version=row["model_version"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )