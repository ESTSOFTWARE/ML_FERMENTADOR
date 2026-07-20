# Configuración

[← Volver al README](../README.md)

## Variables de entorno

Definidas en `src/infrastructure/config/settings.py` (`pydantic-settings`), cargadas desde un archivo `.env` en la raíz del proyecto. **Todas son obligatorias** salvo que se indique lo contrario; si falta alguna, la aplicación falla al arrancar (`Settings()` lanza una excepción de validación).

> ⚠️ Los valores de ejemplo de esta tabla son **placeholders**. Nunca commitear el archivo `.env` real ni credenciales de bases de datos o colas al repositorio (ver `.gitignore`).

| Variable | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `DATA_DIR` | `Path` | Directorio de datasets generados (sintéticos) | `data/generated` |
| `REAL_DATA_DIR` | `Path` | Directorio de datasets/CSVs reales de laboratorio | `data/real` |
| `MODELS_DIR` | `Path` | Directorio donde se guardan/leen los modelos entrenados (`.pkl`) | `models` |
| `DB_HOST` | `str` | Host de PostgreSQL (historial de inferencias) | `localhost` |
| `DB_PORT` | `int` | Puerto de PostgreSQL | `5432` |
| `DB_NAME` | `str` | Nombre de la base de datos | `nichka_ml` |
| `DB_USER` | `str` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD` | `str` | Password de PostgreSQL — **secreto**, no versionar | `<secreto>` |
| `N_FERMENTATIONS` | `int` | Nº de fermentaciones sintéticas a generar en el entrenamiento inicial | `1000` |
| `RANDOM_SEED` | `int` | Semilla para reproducibilidad de la generación sintética | `42` |
| `API_HOST` | `str` | Host de bind de Uvicorn | `0.0.0.0` |
| `API_PORT` | `int` | Puerto de la API | `8000` |
| `API_PREFIX` | `str` | Prefijo común de todas las rutas (excepto `/health`) | `/api/v1` |
| `RABBITMQ_URL` | `str` | URL de conexión AMQP (RabbitMQ/CloudAMQP) — **secreto**, no versionar | `amqp://user:pass@host/vhost` |
| `RABBITMQ_QUEUE` | `str` | Cola de la que se consumen lecturas de sensores en tiempo real | `sensor.readings` |
| `BACKEND_BASE_URL` | `str` | URL base del backend principal Nich-Ká | `http://host.docker.internal:8000` |
| `BACKEND_REPORTS_ENDPOINT` | `str` | Ruta relativa para consultar reportes de fermentación | `/api/fermentation-reports` |
| `BACKEND_SENSORS_ENDPOINT` | `str` | Ruta relativa para consultar el historial de lecturas de sensores | `/api/sensor-readings` |
| `BACKEND_NOTIFICATIONS_ENDPOINT` | `str` | Ruta relativa donde se publican resultados de predicción/anomalía | `/api/notifications/ml-results` |
| `BACKEND_API_TIMEOUT_SECONDS` | `float` | Timeout (segundos) para las llamadas HTTP al backend | `10.0` |
| `DEBUG` | `bool` | Habilita `/docs`, `/redoc` y `/openapi.json` cuando es `true` | `False` |

### Archivo `.env.example` sugerido

```dotenv
DATA_DIR=data/generated
REAL_DATA_DIR=data/real
MODELS_DIR=models

DB_HOST=localhost
DB_PORT=5432
DB_NAME=nichka_ml
DB_USER=postgres
DB_PASSWORD=changeme

N_FERMENTATIONS=1000
RANDOM_SEED=42

API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

RABBITMQ_URL=amqp://guest:guest@localhost/
RABBITMQ_QUEUE=sensor.readings

BACKEND_BASE_URL=http://localhost:8000
BACKEND_REPORTS_ENDPOINT=/api/fermentation-reports
BACKEND_SENSORS_ENDPOINT=/api/sensor-readings
BACKEND_NOTIFICATIONS_ENDPOINT=/api/notifications/ml-results
BACKEND_API_TIMEOUT_SECONDS=10.0

DEBUG=True
```

## Dependencias y librerías

Definidas en `requirements.txt`.

### API / Web

| Librería | Versión | Uso |
|---|---|---|
| `fastapi` | `0.111.0` | Framework HTTP, definición de rutas y validación |
| `uvicorn[standard]` | `0.29.0` | Servidor ASGI |
| `pydantic` | `2.7.1` | Modelado y validación de DTOs |
| `pydantic-settings` | `2.2.1` | Carga de configuración desde `.env` |
| `httpx` | `0.27.0` | Cliente HTTP hacia el backend principal |

### Machine Learning / científico

| Librería | Versión | Uso |
|---|---|---|
| `xgboost` | `2.0.3` | Modelo de predicción de eficiencia (`XGBRegressor`) |
| `scikit-learn` | `1.4.2` | `IsolationForest`, `StandardScaler`, métricas, `train_test_split` |
| `numpy` | `1.26.4` | Cómputo numérico / vectores |
| `pandas` | `2.2.2` | Manipulación tabular de datasets |
| `scipy` | `1.13.0` | Integración de EDOs del simulador cinético (`odeint`) |
| `joblib` | `1.4.2` | Serialización de modelos y scalers |

### Datos / archivos

| Librería | Versión | Uso |
|---|---|---|
| `pyarrow` | `16.1.0` | Lectura/escritura de datasets Parquet |
| `openpyxl` | `3.1.2` | Lectura de archivos Excel (`.xlsx`) de laboratorio |

### Base de datos

| Librería | Versión | Uso |
|---|---|---|
| `psycopg2-binary` | `2.9.9` | Driver PostgreSQL (historial de inferencias) |

### Mensajería y tareas programadas

| Librería | Versión | Uso |
|---|---|---|
| `aio-pika` | `9.4.1` | Cliente asíncrono RabbitMQ (consumo de lecturas en tiempo real) |
| `apscheduler` | `3.10.4` | Job cron para el reentrenamiento nocturno |

## Archivos de configuración relevantes

| Archivo | Propósito |
|---|---|
| `.env` | Variables de entorno locales (no versionado) |
| `src/infrastructure/config/settings.py` | Definición tipada de la configuración (`Settings`) |
| `requirements.txt` | Dependencias de Python |
| `Dockerfile` | Build de la imagen y variables de entorno por defecto para el build |
| `.dockerignore` | Exclusiones del contexto de build de Docker |
| `.gitignore` | Exclusiones del control de versiones |