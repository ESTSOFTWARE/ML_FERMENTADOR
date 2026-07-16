FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/generated data/real models

# Variables mínimas para que Settings() no falle durante el build;
# las reales las inyecta Railway en tiempo de ejecución.
ENV DATA_DIR=data/generated \
    REAL_DATA_DIR=data/real \
    MODELS_DIR=models \
    N_FERMENTATIONS=500 \
    RANDOM_SEED=42 \
    API_HOST=0.0.0.0 \
    API_PORT=8001 \
    API_PREFIX=/api/v1 \
    DB_HOST=localhost \
    DB_PORT=5432 \
    DB_NAME=ml \
    DB_USER=ml \
    DB_PASSWORD=ml \
    RABBITMQ_URL=amqp://guest:guest@localhost/ \
    RABBITMQ_QUEUE=ml_queue \
    BACKEND_BASE_URL=http://localhost:8000 \
    BACKEND_REPORTS_ENDPOINT=/api/fermentation/reports \
    BACKEND_SENSORS_ENDPOINT=/api/sensors/history \
    BACKEND_NOTIFICATIONS_ENDPOINT=/api/notifications/push \
    BACKEND_API_TIMEOUT_SECONDS=10.0 \
    DEBUG=false

RUN python scripts/train_initial_models.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]