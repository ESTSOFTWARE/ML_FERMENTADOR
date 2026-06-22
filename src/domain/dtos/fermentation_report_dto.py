from datetime import datetime

from pydantic import BaseModel


class FermentationReportDTO(BaseModel):
    """
    Espejo de la tabla fermentation_reports del backend.
    Es la fuente de verdad para el reentrenamiento incremental
    (retrain_with_real_report.py) cuando una fermentación termina.
    """

    session_id: int
    group_id: int | None = None
    """Opcional. Permite segmentar reentrenamiento por salón/grupo
    en el futuro (fermentation_sessions.group_id -> classrooms)."""

    initial_sugar: float
    final_sugar: float | None = None
    ethanol_detected: float | None = None
    theoretical_ethanol: float | None = None
    efficiency: float | None = None

    alcohol_initial: float | None = None
    alcohol_final: float | None = None
    alcohol_last_reading: float | None = None

    density_initial: float | None = None
    density_final: float | None = None
    density_last_reading: float | None = None

    conductivity_initial: float | None = None
    conductivity_final: float | None = None
    conductivity_last_reading: float | None = None

    ph_initial: float | None = None
    ph_final: float | None = None
    ph_last_reading: float | None = None

    temperature_initial: float | None = None
    temperature_final: float | None = None
    temperature_last_reading: float | None = None

    turbidity_initial: float | None = None
    turbidity_final: float | None = None
    turbidity_last_reading: float | None = None

    rpm_initial: float | None = None
    rpm_final: float | None = None
    rpm_last_reading: float | None = None

    notes: str | None = None
    generated_at: datetime