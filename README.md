# Nicka ML Service

Un servicio de machine learning moderno y escalable.

## Descripción

Este proyecto proporciona funcionalidades de machine learning para procesamiento de datos, entrenamiento de modelos e inferencia en tiempo real.

## Requisitos

- Python 3.8+
- Docker
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/ESTSOFTWARE/ML_FERMENTADOR.git
cd nicka-ml-service
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar localmente

```bash
python main.py
```

### Usar Docker

```bash
docker-compose up --build
```

## Estructura del Proyecto

```
├── src/               # Código fuente principal
├── data/              # Datos (generados y reales)
├── models/            # Modelos entrenados
├── scripts/           # Scripts de utilidad
├── tests/             # Tests
└── main.py            # Punto de entrada
```

## Configuración

Las variables de entorno se configuran en el archivo `.env`. Asegúrate de crear este archivo con las configuraciones necesarias.

## API

El servicio expone endpoints HTTP para:
- Predicciones
- Detección de anomalías
- Entrenamiento de modelos
- Procesamiento en tiempo real

Consulta la documentación de rutas para más detalles.

## Testing

```bash
docker compose exec nicka-ml python -m scripts.train_initial_models
```

## Payloads para testing (Local)

```bash
curl -X POST http://localhost:8000/api/v1/predict/efficiency \
  -H "Content-Type: application/json" \
  -d '{
    "time_hours": [0, 4, 8, 12, 24, 36, 48],
    "ph": [4.60, 4.68, 4.74, 4.78, 4.85, 4.89, 4.91],
    "temperature_c": [30.1, 29.9, 30.0, 30.2, 30.0, 29.8, 30.1],
    "turbidity": [3.85, 4.10, 4.55, 5.20, 6.80, 8.90, 10.50],
    "conductivity": [1998, 1950, 1890, 1810, 1620, 1400, 1180],
    "alcohol_percent": [0.0, 0.17, 0.40, 0.68, 1.79, 2.34, 2.95]
  }'

```

```bash
curl -X POST http://localhost:8000/api/v1/detect/anomaly \-X POST http://localhost:8000/api/v1/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{
    "current": {"ph": 4.78, "temperature_c": 30.1, "turbidity": 5.20, "conductivity": 1810, "alcohol_percent": 0.68},
    "history_hours": [0, 2, 4, 6, 8, 10],
    "history": [
      {"ph": 4.60, "temperature_c": 30.0, "turbidity": 3.85, "conductivity": 1998, "alcohol_percent": 0.0},
      {"ph": 4.63, "temperature_c": 30.1, "turbidity": 3.95, "conductivity": 1970, "alcohol_percent": 0.05},
      {"ph": 4.68, "temperature_c": 29.9, "turbidity": 4.10, "conductivity": 1950, "alcohol_percent": 0.17},
      {"ph": 4.71, "temperature_c": 30.0, "turbidity": 4.25, "conductivity": 1920, "alcohol_percent": 0.30},
      {"ph": 4.74, "temperature_c": 30.2, "turbidity": 4.55, "conductivity": 1890, "alcohol_percent": 0.40},
      {"ph": 4.76, "temperature_c": 30.0, "turbidity": 4.85, "conductivity": 1850, "alcohol_percent": 0.55}
    ]
  }'
```

```bash
curl -X POST http://localhost:8000/api/v1/realtime/reading \//localhost:8000/api/v1/realtime/reading \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "circuit_id": 1,
    "timestamp": "2026-06-21T10:00:00",
    "current": {"ph": 4.78, "temperature_c": 30.1, "turbidity": 5.20, "conductivity": 1810, "alcohol_percent": 0.68},
    "history_hours": [0, 2, 4, 6, 8, 10],
    "history": [
      {"ph": 4.60, "temperature_c": 30.0, "turbidity": 3.85, "conductivity": 1998, "alcohol_percent": 0.0},
      {"ph": 4.63, "temperature_c": 30.1, "turbidity": 3.95, "conductivity": 1970, "alcohol_percent": 0.05},
      {"ph": 4.68, "temperature_c": 29.9, "turbidity": 4.10, "conductivity": 1950, "alcohol_percent": 0.17},
      {"ph": 4.71, "temperature_c": 30.0, "turbidity": 4.25, "conductivity": 1920, "alcohol_percent": 0.30},
      {"ph": 4.74, "temperature_c": 30.2, "turbidity": 4.55, "conductivity": 1890, "alcohol_percent": 0.40},
      {"ph": 4.76, "temperature_c": 30.0, "turbidity": 4.85, "conductivity": 1850, "alcohol_percent": 0.55}
    ],
    "elapsed_hours": 10,
    "planned_duration_hours": 120
  }'
```