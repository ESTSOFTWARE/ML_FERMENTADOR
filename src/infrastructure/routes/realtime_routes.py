from fastapi import APIRouter, Depends, HTTPException

from src.domain.dtos.realtime_reading_dto import RealtimeReadingDTO
from src.infrastructure.controllers.realtime_controller import RealtimeController
from src.infrastructure.dependencies import get_realtime_controller

router = APIRouter(prefix="/realtime", tags=["Tiempo real"])


@router.post("/reading")
def process_reading(
    reading: RealtimeReadingDTO,
    controller: RealtimeController = Depends(get_realtime_controller),
) -> dict:
    """
    El backend llama aquí cada vez que llega una lectura nueva de
    sensores (vía RabbitMQ desde el ESP32) para una sesión con
    status='running'. Dispara detección de anomalías siempre, y
    predicción de eficiencia si ya se alcanzó el 50% del tiempo
    planeado. Ambos resultados se publican de vuelta al backend
    para reenviarse por WebSocket al frontend.
    """
    try:
        return controller.handle(reading)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc