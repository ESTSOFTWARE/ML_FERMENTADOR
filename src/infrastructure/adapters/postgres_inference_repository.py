from datetime import datetime
from uuid import UUID

import psycopg2
import psycopg2.extras

from src.domain.entities.anomaly_inference import AnomalyInference
from src.domain.repositories.inference_repository import InferenceRepository
from src.infrastructure.config.settings import settings

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS anomaly_inferences (
    inference_id    UUID PRIMARY KEY,
    session_id      INTEGER,
    circuit_id      INTEGER,
    timestamp       TIMESTAMPTZ NOT NULL,
    ph              DOUBLE PRECISION NOT NULL,
    temperature_c   DOUBLE PRECISION NOT NULL,
    turbidity       DOUBLE PRECISION NOT NULL,
    conductivity    DOUBLE PRECISION NOT NULL,
    alcohol_percent DOUBLE PRECISION NOT NULL,
    history_length  INTEGER NOT NULL,
    is_anomaly      BOOLEAN NOT NULL,
    anomaly_score   DOUBLE PRECISION NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL
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
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


class PostgresInferenceRepository(InferenceRepository):
    def __init__(self) -> None:
        self._dsn = (
            f"host={settings.db_host} port={settings.db_port} "
            f"dbname={settings.db_name} user={settings.db_user} "
            f"password={settings.db_password}"
        )
        self._initialize()

    def _connect(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(self._dsn)

    def _initialize(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)

    def save(self, inference: AnomalyInference) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(INSERT_SQL, (
                    str(inference.id),
                    inference.session_id,
                    inference.circuit_id,
                    inference.timestamp,
                    inference.ph,
                    inference.temperature_c,
                    inference.turbidity,
                    inference.conductivity,
                    inference.alcohol_percent,
                    inference.history_length,
                    inference.is_anomaly,
                    inference.anomaly_score,
                    inference.model_version,
                    inference.created_at,
                ))

    def get_all(self, limit: int = 100) -> list[AnomalyInference]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM anomaly_inferences ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                return [self._to_entity(row) for row in cur.fetchall()]

    def get_by_session_id(self, session_id: int) -> list[AnomalyInference]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM anomaly_inferences WHERE session_id = %s ORDER BY created_at DESC",
                    (session_id,),
                )
                return [self._to_entity(row) for row in cur.fetchall()]

    def get_anomalies_only(self, limit: int = 100) -> list[AnomalyInference]:
        with self._connect() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM anomaly_inferences WHERE is_anomaly = TRUE ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                return [self._to_entity(row) for row in cur.fetchall()]

    @staticmethod
    def _to_entity(row: psycopg2.extras.RealDictRow) -> AnomalyInference:
        return AnomalyInference(
            id=UUID(str(row["inference_id"])),
            session_id=row["session_id"],
            circuit_id=row["circuit_id"],
            timestamp=row["timestamp"],
            ph=row["ph"],
            temperature_c=row["temperature_c"],
            turbidity=row["turbidity"],
            conductivity=row["conductivity"],
            alcohol_percent=row["alcohol_percent"],
            history_length=row["history_length"],
            is_anomaly=row["is_anomaly"],
            anomaly_score=row["anomaly_score"],
            model_version=row["model_version"],
            created_at=row["created_at"],
        )
