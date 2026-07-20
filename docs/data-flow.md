# Flujo de procesamiento de datos

[← Volver al README](../README.md)

Este documento describe los cuatro flujos de datos del servicio: generación de datasets, entrenamiento inicial, inferencia en tiempo real, y reentrenamiento incremental.

## 1. Generación de datasets de entrenamiento

Existen tres fuentes de datos para entrenar los modelos, todas convergen al mismo formato de registro (una fila por timestamp, con columnas de sensores + `is_anomaly` + `final_efficiency_percent`):

```mermaid
flowchart TB
    subgraph Sintético
        A1["GenerateSyntheticDataset"] --> A2["SimulateFermentation\n(EDO: modelo Logístico/Monod)"]
        A2 --> A3["Ruido instrumental +\ninyección de anomalías\n(stuck_ph, temp_spike,\nconductivity_jump, stuck_alcohol)"]
    end
    subgraph "CSV real de laboratorio"
        B1["BuildDatasetFromCsv"] --> B2["CsvSensorReadingRepository"]
        B2 --> B3["ReadingsToProfile\n(pivot + interpolación)"]
    end
    subgraph "Reportes reales completados"
        C1["BuildDatasetFromReports"] --> C2["FermentationReportRepository (HTTP)"]
    end
    subgraph "Archivo de laboratorio (upload)"
        D1["LabFileReader\n(detecta formato: kinetic / wide)"] --> D2["LabFileToProfile"]
    end

    A3 --> R["Registros de entrenamiento\n(FermentationProfile.to_records())"]
    B3 --> R
    D2 --> R
    C2 --> RC["Registro resumen\n(sin serie de tiempo completa)"]
```

- **Sintético** (`scripts/train_initial_models.py`, `GenerateSyntheticDataset`): resuelve las EDO del modelo cinético (Logístico calibrado con R²=0.9955, o Monod) con `scipy.odeint`, convierte biomasa/azúcar/etanol a lecturas de sensor (`SensorProfileMapper`), agrega ruido gaussiano + deriva, e inyecta anomalías en ~10 % de las fermentaciones (tasa `ANOMALY_RATE`).
- **CSV real** (`BuildDatasetFromCsv`): lee un CSV de formato ancho (una columna por sensor) y lo convierte a perfil vía `ReadingsToProfile`.
- **Archivo de laboratorio subido** (`/training/*/upload`): `LabFileReader` detecta si el archivo es formato `kinetic` (columnas crudas de laboratorio: azúcares/etanol reales — permite reconstruir biomasa por balance de masa y calcular la eficiencia real) o `wide` (ya son lecturas de sensor, requiere `efficiency_override` explícito porque no trae azúcar/etanol).
- **Reportes reales** (`BuildDatasetFromReports`): a diferencia de las otras fuentes, produce un registro resumen (valores inicial/final/última lectura), sin serie de tiempo completa — se usa principalmente para análisis agregado, no para entrenar directamente los modelos de series de tiempo.

## 2. Entrenamiento inicial

```mermaid
sequenceDiagram
    participant S as scripts/train_initial_models.py
    participant G as GenerateSyntheticDataset
    participant FE as Feature Extractors
    participant T as Train*Model
    participant MR as ModelRepository (joblib)

    S->>G: execute(n=N_FERMENTATIONS)
    G-->>S: registros sintéticos
    S->>FE: ExtractPredictionFeatures / ExtractAnomalyFeatures
    FE-->>S: features (54 / 10 columnas)
    S->>T: TrainEfficiencyModel.execute() / TrainAnomalyModel.execute()
    T-->>S: modelo, scaler, metrics
    S->>MR: save(modelo), save(scaler)
```

Este flujo corre en el `Dockerfile` durante el *build* de la imagen (`RUN python scripts/train_initial_models.py`), garantizando que el servicio arranque con modelos base disponibles.

## 3. Inferencia en tiempo real

Es el flujo principal en producción: por cada lectura de sensores de una sesión activa, se ejecuta **siempre** la detección de anomalías, y la **predicción de eficiencia solo si ya se alcanzó el 50 % del tiempo planeado** de la fermentación.

```mermaid
sequenceDiagram
    participant Src as Backend / RabbitMQ
    participant Ctrl as RealtimeController / RabbitMQConsumer
    participant P as ProcessRealtimeReading
    participant DA as DetectAnomaly
    participant PE as PredictEfficiency
    participant DB as PostgreSQL
    participant Pub as NotificationPublisher
    participant BE as Backend principal

    Src->>Ctrl: RealtimeReadingDTO
    Ctrl->>P: execute(reading)
    P->>DA: execute(current + historial 2h)
    DA->>DB: guarda AnomalyInference
    DA-->>P: is_anomaly, score
    P->>Pub: publish_anomaly_result()
    Pub->>BE: POST /notifications (type=anomaly)

    alt elapsed_hours >= 50% planned_duration_hours
        P->>PE: execute(ventana primer 50%)
        PE-->>P: efficiency_percent
        P->>Pub: publish_efficiency_result()
        Pub->>BE: POST /notifications (type=efficiency)
    end

    P-->>Ctrl: {session_id, anomaly_detected, efficiency_predicted}
```

Dos vías de entrada equivalentes disparan este mismo flujo:

1. **HTTP**: `POST /api/v1/realtime/reading`, llamado por el backend.
2. **RabbitMQ**: `RabbitMQConsumer` escuchando la cola `RABBITMQ_QUEUE`, para el camino asíncrono desde los sensores (ESP32).

## 4. Reentrenamiento incremental

Dos vías:

- **Puntual**, disparado por el backend cuando una fermentación termina: `POST /training/report-completed` → `RetrainWithRealReport` (eficiencia) — este endpoint específico no ejecuta el reentrenamiento de anomalías, solo el de eficiencia. El de anomalías (`RetrainAnomalyWithRealReport`) se ejecuta como parte del batch nocturno.
- **Batch nocturno** (`ScheduledNightlyRetrain`, cron `02:00` vía APScheduler): recorre todos los reportes completados en las últimas 24 h y reentrena **ambos** modelos de forma incremental (warm start), de forma independiente por modelo — un fallo en uno no detiene al otro.

```mermaid
flowchart TB
    CRON["APScheduler 02:00 AM"] --> SNR["ScheduledNightlyRetrain"]
    SNR --> REP["FermentationReportRepository\n(reportes completados últimas 24h)"]
    REP --> LOOP{"por cada reporte"}
    LOOP --> RE["RetrainWithRealReport\n(XGBoost warm-start)"]
    LOOP --> RA["RetrainAnomalyWithRealReport\n(IsolationForest warm-start)"]
    RE --> MR["ModelRepository.save()"]
    RA --> MR
```

Ambos reentrenamientos reutilizan el **mismo scaler** ya ajustado (no se hace `fit_transform` de nuevo), para mantener consistente la distribución de referencia entre reentrenamientos sucesivos.