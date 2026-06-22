from fastapi import APIRouter, Depends, HTTPException

from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.dtos.anomaly_response_dto import AnomalyResponseDTO
from src.infrastructure.controllers.anomaly_controller import AnomalyController
from src.infrastructure.dependencies import get_anomaly_controller

router = APIRouter(prefix="/detect", tags=["Anomalías"])


@router.post("/anomaly", response_model=AnomalyResponseDTO)
def detect_anomaly(
    request: AnomalyRequestDTO,
    controller: AnomalyController = Depends(get_anomaly_controller),
) -> AnomalyResponseDTO:
    try:
        return controller.handle(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc