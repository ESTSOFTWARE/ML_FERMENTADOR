from fastapi import FastAPI

from src.infrastructure.config.settings import settings
from src.infrastructure.routes import (
    anomaly_routes,
    inference_routes,
    predict_routes,
    realtime_routes,
    training_routes,
)

app = FastAPI(
    title="Nich-Ká ML Service",
    description=(
        "Microservicio de Machine Learning para el sistema Nich-Ká: "
        "predicción de eficiencia y detección de anomalías en fermentaciones."
    ),
    version="1.0.0",
)

app.include_router(predict_routes.router, prefix=settings.api_prefix)
app.include_router(anomaly_routes.router, prefix=settings.api_prefix)
app.include_router(realtime_routes.router, prefix=settings.api_prefix)
app.include_router(training_routes.router, prefix=settings.api_prefix)
app.include_router(inference_routes.router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}