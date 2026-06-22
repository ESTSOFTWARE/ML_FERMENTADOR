from pydantic import BaseModel


class EfficiencyResponseDTO(BaseModel):
    """Respuesta del endpoint POST /predict/efficiency."""

    efficiency_percent: float
    model_version: str = "1.0.0"