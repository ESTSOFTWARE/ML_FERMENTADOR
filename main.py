from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from src.infrastructure.adapters.rabbitmq_consumer import RabbitMQConsumer
from src.infrastructure.config.settings import settings
from src.infrastructure.dependencies import get_nightly_retrain_use_case, get_realtime_use_case
from src.infrastructure.routes import (
    anomaly_routes,
    inference_routes,
    predict_routes,
    realtime_routes,
    training_routes,
)
from src.infrastructure.adapters.mqtt_sensor_consumer import MqttSensorConsumer
from src.infrastructure.dependencies import (
    get_nightly_retrain_use_case,
    get_process_mqtt_sensor_reading,
    get_realtime_use_case,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer = RabbitMQConsumer(get_realtime_use_case())
    await consumer.start()

    mqtt_sensor_consumer = MqttSensorConsumer(get_process_mqtt_sensor_reading())
    await mqtt_sensor_consumer.start()
    
    scheduler = AsyncIOScheduler()
    nightly_retrain = get_nightly_retrain_use_case()
    scheduler.add_job(
        nightly_retrain.execute,
        trigger=CronTrigger(hour=2, minute=0),
        id="nightly_retrain",
        name="Reentrenamiento nocturno 2AM",
        replace_existing=True,
    )
    scheduler.start()

    yield

    await consumer.stop()
    await mqtt_sensor_consumer.stop()
    scheduler.shutdown()


app = FastAPI(
    title="Nich-Ká ML Service",
    description=(
        "Microservicio de Machine Learning para el sistema Nich-Ká: "
        "predicción de eficiencia y detección de anomalías en fermentaciones."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

app.include_router(predict_routes.router, prefix=settings.api_prefix)
app.include_router(anomaly_routes.router, prefix=settings.api_prefix)
app.include_router(realtime_routes.router, prefix=settings.api_prefix)
app.include_router(training_routes.router, prefix=settings.api_prefix)
app.include_router(inference_routes.router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}