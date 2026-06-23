from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class AnomalyInference:
    """
    Representa una inferencia de anomalía ejecutada por el modelo
    Isolation Forest. Es la entidad que se persiste en la BD local.
    """

    session_id: int | None
    circuit_id: int | None
    timestamp: datetime
    ph: float
    temperature_c: float
    turbidity: float
    conductivity: float
    alcohol_percent: float
    history_length: int
    is_anomaly: bool
    anomaly_score: float
    model_version: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "inference_id": str(self.id),
            "session_id": self.session_id,
            "circuit_id": self.circuit_id,
            "timestamp": self.timestamp.isoformat(),
            "ph": self.ph,
            "temperature_c": self.temperature_c,
            "turbidity": self.turbidity,
            "conductivity": self.conductivity,
            "alcohol_percent": self.alcohol_percent,
            "history_length": self.history_length,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(),
        }