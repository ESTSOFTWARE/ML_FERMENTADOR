# API — Endpoints

[← Volver al README](../README.md)

Todos los endpoints (salvo `/health`) están montados bajo el prefijo configurado en `API_PREFIX` (por defecto `/api/v1`). La documentación interactiva (Swagger/Redoc) solo está disponible cuando `DEBUG=true` (`/docs`, `/redoc`, `/openapi.json`); en producción (`DEBUG=false`) quedan deshabilitadas.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| POST | `{prefix}/predict/efficiency` | Predicción de eficiencia final |
| POST | `{prefix}/detect/anomaly` | Detección síncrona de anomalía |
| POST | `{prefix}/realtime/reading` | Procesamiento de una lectura en tiempo real (predicción + detección + notificación) |
| POST | `{prefix}/training/report-completed` | Reentrenamiento incremental de eficiencia con un reporte real |
| POST | `{prefix}/training/efficiency/upload` | Entrenamiento del modelo de eficiencia desde archivos |
| POST | `{prefix}/training/anomaly/upload` | Entrenamiento del modelo de anomalías desde archivos |
| GET | `{prefix}/inferences/` | Historial de inferencias de anomalía |
| GET | `{prefix}/inferences/anomalies` | Historial, solo anomalías detectadas |
| GET | `{prefix}/inferences/session/{{session_id}}` | Historial de inferencias de una sesión |

---

## GET `/health`

Health check simple, sin prefijo de API.

**Respuesta `200 OK`**
```json
{ "status": "ok" }
```

---

## POST `{prefix}/predict/efficiency`

Predice la eficiencia final de una fermentación a partir de la serie de tiempo del primer 50 % del proceso.

**Cuerpo de la solicitud** (`SensorWindowDTO`)

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `time_hours` | `float[]` | Sí | Mínimo 2 elementos |
| `ph` | `float[]` | Sí | Misma longitud que `time_hours` |
| `temperature_c` | `float[]` | Sí | Misma longitud que `time_hours` |
| `turbidity` | `float[]` | Sí | Misma longitud que `time_hours` |
| `conductivity` | `float[]` | Sí | Misma longitud que `time_hours` |
| `alcohol_percent` | `float[]` | Sí | Misma longitud que `time_hours` |

```json
{
  "time_hours": [0, 4, 8, 12, 24, 36, 48],
  "ph": [4.60, 4.68, 4.74, 4.78, 4.85, 4.89, 4.91],
  "temperature_c": [30.1, 29.9, 30.0, 30.2, 30.0, 29.8, 30.1],
  "turbidity": [3.85, 4.10, 4.55, 5.20, 6.80, 8.90, 10.50],
  "conductivity": [1998, 1950, 1890, 1810, 1620, 1400, 1180],
  "alcohol_percent": [0.0, 0.17, 0.40, 0.68, 1.79, 2.34, 2.95]
}
```

**Respuesta `200 OK`** (`EfficiencyResponseDTO`)
```json
{
  "efficiency_percent": 87.42,
  "model_version": "1.0.0"
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Predicción exitosa |
| `422` | Cuerpo inválido (listas de distinta longitud, tipos incorrectos, `time_hours` con menos de 2 elementos) |
| `503` | El modelo de eficiencia todavía no ha sido entrenado (`FileNotFoundError`) |

---

## POST `{prefix}/detect/anomaly`

Detección síncrona de anomalía (fuera del flujo de tiempo real orquestado). No persiste `session_id`/`circuit_id` porque no se reciben en este endpoint.

**Cuerpo de la solicitud** (`AnomalyRequestDTO`)

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `current` | `SensorSnapshotDTO` | Sí | `ph`, `temperature_c`, `turbidity`, `conductivity`, `alcohol_percent` |
| `history_hours` | `float[]` | Sí | Mínimo 1 elemento |
| `history` | `SensorSnapshotDTO[]` | Sí | Mínimo 1 elemento, misma longitud que `history_hours` |

```json
{
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
}
```

**Respuesta `200 OK`** (`AnomalyResponseDTO`)
```json
{
  "is_anomaly": false,
  "anomaly_score": 0.0421
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Detección exitosa |
| `422` | Cuerpo inválido |
| `503` | El modelo de anomalías todavía no ha sido entrenado |

---

## POST `{prefix}/realtime/reading`

Endpoint principal del flujo en tiempo real. El backend lo invoca cada vez que llega una lectura nueva de sensores para una sesión con `status='running'` (vía RabbitMQ desde el ESP32). Ejecuta **siempre** detección de anomalías y, si `elapsed_hours` ya alcanzó el 50 % de `planned_duration_hours`, también predicción de eficiencia. Ambos resultados se publican al backend (`BACKEND_NOTIFICATIONS_ENDPOINT`).

**Cuerpo de la solicitud** (`RealtimeReadingDTO`)

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `session_id` | `int` | Sí | |
| `circuit_id` | `int` | Sí | |
| `timestamp` | `datetime` (ISO 8601) | Sí | |
| `current` | `SensorSnapshotDTO` | Sí | |
| `history_hours` | `float[]` | Sí | Misma longitud que `history` |
| `history` | `SensorSnapshotDTO[]` | Sí | Misma longitud que `history_hours` |
| `elapsed_hours` | `float` | Sí | Horas transcurridas desde el inicio real |
| `planned_duration_hours` | `float` | Sí | Debe ser `> 0` |

```json
{
  "session_id": 1,
  "circuit_id": 1,
  "timestamp": "2026-06-21T10:00:00",
  "current": {"ph": 4.78, "temperature_c": 30.1, "turbidity": 5.20, "conductivity": 1810, "alcohol_percent": 0.68},
  "history_hours": [0, 2, 4, 6, 8, 10],
  "history": [
    {"ph": 4.60, "temperature_c": 30.0, "turbidity": 3.85, "conductivity": 1998, "alcohol_percent": 0.0}
  ],
  "elapsed_hours": 10,
  "planned_duration_hours": 120
}
```

**Respuesta `200 OK`**
```json
{
  "session_id": 1,
  "anomaly_detected": false,
  "efficiency_predicted": false
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Procesamiento exitoso |
| `422` | Cuerpo inválido (`planned_duration_hours <= 0`, longitudes de `history`/`history_hours` distintas) |
| `503` | Alguno de los modelos requeridos no está entrenado todavía |

---

## POST `{prefix}/training/report-completed`

Reentrena de forma incremental el modelo de **eficiencia** con una fermentación real recién completada. Lo invoca el backend cuando una sesión finaliza y su reporte ya tiene `efficiency` calculada.

**Cuerpo de la solicitud** (`FermentationReportDTO`, campos principales)

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `session_id` | `int` | Sí | |
| `group_id` | `int \| null` | No | |
| `initial_sugar` | `float` | Sí | |
| `final_sugar` | `float \| null` | No | |
| `ethanol_detected` | `float \| null` | No | |
| `theoretical_ethanol` | `float \| null` | No | |
| `efficiency` | `float \| null` | No | Requerido en la práctica: sin él el reentrenamiento falla |
| `*_initial`, `*_final`, `*_last_reading` | `float \| null` | No | Para `alcohol`, `density`, `conductivity`, `ph`, `temperature`, `turbidity`, `rpm` |
| `notes` | `string \| null` | No | |
| `generated_at` | `datetime` | Sí | |

**Respuesta `200 OK`**
```json
{
  "session_id": 1,
  "retrained_with_efficiency": 87.42,
  "n_readings_used": 342,
  "status": "model_updated"
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Reentrenamiento exitoso |
| `422` | `efficiency` ausente en el reporte, o no existe un modelo base entrenado todavía (`ValueError` / `FileNotFoundError`) |

---

## POST `{prefix}/training/efficiency/upload`

Entrena **desde cero** el modelo de eficiencia con uno o más archivos de laboratorio (`multipart/form-data`).

**Parámetros (form-data)**

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `files` | `file[]` (`.csv`, `.xlsx`, `.xls`) | Sí | Un archivo por fermentación |
| `fermentation_ids` | `string[]` | No | Mismo orden y longitud que `files`; si se omite se autogeneran |
| `efficiencies` | `float[]` | Condicional | **Requerido** para archivos formato `wide` (no traen azúcar/etanol reales); mismo orden que `files` |

**Respuesta `200 OK`**
```json
{
  "n_fermentations": 3,
  "metrics": {
    "mae": 2.14,
    "rmse": 3.02,
    "r2": 0.91,
    "n_samples": 3,
    "validated": false,
    "warning": "Entrenado con solo 3 muestra(s), sin split de validación/test..."
  },
  "status": "model_trained"
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Entrenamiento exitoso |
| `422` | Extensión de archivo no soportada, longitudes de `fermentation_ids`/`efficiencies` inconsistentes con `files`, archivo `wide` sin `efficiencies`, o cero archivos enviados |

---

## POST `{prefix}/training/anomaly/upload`

Entrena **desde cero** el modelo de anomalías (Isolation Forest) con uno o más archivos de laboratorio. Todas las filas de los archivos subidos se consideran datos normales (`is_anomaly=False`).

**Parámetros (form-data)**

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `files` | `file[]` (`.csv`, `.xlsx`, `.xls`) | Sí | Un archivo por fermentación |
| `fermentation_ids` | `string[]` | No | Mismo orden y longitud que `files` |

**Respuesta `200 OK`**
```json
{
  "n_fermentations": 2,
  "n_rows": 220,
  "metrics": {
    "precision": 0.0,
    "recall": 0.0,
    "f1": 0.0,
    "n_windows": 200,
    "validated": true
  },
  "status": "model_trained"
}
```

**Códigos de estado**

| Código | Causa |
|---|---|
| `200` | Entrenamiento exitoso |
| `422` | Extensión no soportada, `fermentation_ids` con longitud inconsistente, o no se generó ninguna ventana de entrenamiento (fermentaciones con menos de 2 puntos de tiempo) |

---

## GET `{prefix}/inferences/`

Consulta el historial de inferencias de anomalía almacenadas en PostgreSQL.

**Query params**

| Parámetro | Tipo | Requerido | Default | Rango |
|---|---|---|---|---|
| `limit` | `int` | No | `100` | `1`–`1000` |

**Respuesta `200 OK`** — lista de objetos `AnomalyInference.to_dict()`:
```json
[
  {
    "inference_id": "b1e2...",
    "session_id": 1,
    "circuit_id": 1,
    "timestamp": "2026-06-21T10:00:00",
    "ph": 4.78,
    "temperature_c": 30.1,
    "turbidity": 5.20,
    "conductivity": 1810.0,
    "alcohol_percent": 0.68,
    "history_length": 6,
    "is_anomaly": false,
    "anomaly_score": 0.0421,
    "model_version": "1.0.0",
    "created_at": "2026-06-21T10:00:01.123456"
  }
]
```

**Códigos de estado:** `200` (éxito), `422` (`limit` fuera de rango).

## GET `{prefix}/inferences/anomalies`

Igual al anterior, filtrado a `is_anomaly = true`. Mismo `limit` (query param, `1`–`1000`, default `100`) y mismo formato de respuesta.

## GET `{prefix}/inferences/session/{session_id}`

Historial de inferencias de una sesión específica, sin paginación (`session_id` como parámetro de ruta, `int`).

**Códigos de estado:** `200` (éxito, puede devolver lista vacía si la sesión no tiene inferencias).