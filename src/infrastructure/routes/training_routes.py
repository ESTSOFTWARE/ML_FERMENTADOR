from fastapi import APIRouter, Depends, HTTPException

from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.infrastructure.controllers.training_controller import TrainingController
from src.infrastructure.dependencies import get_training_controller

router = APIRouter(prefix="/training", tags=["Entrenamiento"])


@router.post("/report-completed")
def report_completed(
    report: FermentationReportDTO,
    controller: TrainingController = Depends(get_training_controller),
) -> dict:
    """
    Webhook: el backend llama aquí cuando una fermentación termina
    (fermentation_sessions.status pasa a 'completed' y se genera el
    fermentation_reports correspondiente).
    """
    try:
        return controller.handle_report_completed(report)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc