from fastapi import APIRouter, Depends, Query

from src.infrastructure.controllers.inference_controller import InferenceController
from src.infrastructure.dependencies import get_inference_controller

router = APIRouter(prefix="/inferences", tags=["Historial de inferencias"])


@router.get(
    "/",
    summary="Consultar historial de inferencias",
    description="Devuelve las últimas inferencias de anomalía almacenadas en la BD local.",
)
def get_all(
    limit: int = Query(default=100, ge=1, le=1000),
    controller: InferenceController = Depends(get_inference_controller),
) -> list[dict]:
    return controller.get_all(limit=limit)


@router.get(
    "/anomalies",
    summary="Consultar solo inferencias con anomalía detectada",
)
def get_anomalies_only(
    limit: int = Query(default=100, ge=1, le=1000),
    controller: InferenceController = Depends(get_inference_controller),
) -> list[dict]:
    return controller.get_anomalies_only(limit=limit)


@router.get(
    "/session/{session_id}",
    summary="Consultar inferencias de una sesión de fermentación específica",
)
def get_by_session(
    session_id: int,
    controller: InferenceController = Depends(get_inference_controller),
) -> list[dict]:
    return controller.get_by_session(session_id)