from fastapi import APIRouter, Depends, HTTPException

from src.domain.dtos.efficiency_response_dto import EfficiencyResponseDTO
from src.domain.dtos.sensor_window_dto import SensorWindowDTO
from src.infrastructure.controllers.predict_controller import PredictController
from src.infrastructure.dependencies import get_predict_controller

router = APIRouter(prefix="/predict", tags=["Predicción"])


@router.post("/efficiency", response_model=EfficiencyResponseDTO)
def predict_efficiency(
    window: SensorWindowDTO,
    controller: PredictController = Depends(get_predict_controller),
) -> EfficiencyResponseDTO:
    try:
        return controller.handle(window)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc