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

## 3. Inferencia en tiempo real — flujo combinado (predicción + anomalía)

Flujo activado por el backend cuando ya tiene una lectura ensamblada: se ejecuta **siempre** la detección de anomalías, y la **predicción de eficiencia solo si ya se alcanzó el 50 % del tiempo planeado** de la fermentación.

```mermaid
sequenceDiagram
    participant Src as Backend / RabbitMQ (RABBITMQ_QUEUE)
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
2. **RabbitMQ**: `RabbitMQConsumer` escuchando la cola `RABBITMQ_QUEUE`, con el `RealtimeReadingDTO` ya armado por el backend.

Este flujo sigue siendo la única vía para la **predicción de eficiencia** (necesita `elapsed_hours`/`planned_duration_hours`, que solo conoce el backend). Para anomalías, ver la sección siguiente.

## 3.1. Detección de anomalías dedicada — datos crudos de sensores (`mqtt.sensor.data.queue`)

Camino **independiente** del anterior, pensado para que la detección de anomalías reaccione a cada lectura real de sensor sin esperar a que el backend arme nada — es el flujo verdaderamente en tiempo real del Isolation Forest.

A diferencia de `RABBITMQ_QUEUE`, esta cola recibe **un mensaje por sensor individual** (`circuit_id`, `sensor_type`, `value`, `active`, `session_id`, `timestamp`), publicado directamente por el bridge MQTT → RabbitMQ. Por eso hace falta reconstruir el snapshot completo (los 5 sensores) en memoria antes de poder correr el modelo.

```mermaid
sequenceDiagram
    participant ESP32 as Sensores / ESP32 (bridge MQTT)
    participant Q as RabbitMQ (mqtt.sensor.data.queue)
    participant C as MqttSensorConsumer
    participant P as ProcessMqttSensorReading
    participant State as CircuitSensorStateRepository (memoria)
    participant DA as DetectAnomaly
    participant DB as PostgreSQL
    participant Pub as NotificationPublisher
    participant BE as Backend principal

    ESP32->>Q: {circuit_id, sensor_type, value, active, session_id, timestamp}
    Q->>C: mensaje (un sensor)
    C->>C: descarta si active=false\no si sensor_type no es de interés (density, rpm)
    C->>P: execute(circuit_id, session_id, timestamp, field, value)
    P->>State: update_latest(circuit_id, field, value)
    P->>State: get_latest_snapshot(circuit_id, campos requeridos)

    alt aún falta el primer valor de algún sensor
        State-->>P: None
        Note over P: se omite este ciclo, sin correr el modelo
    else snapshot completo
        State-->>P: SensorSnapshotDTO
        P->>State: add_snapshot(circuit_id, timestamp, snapshot)
        P->>State: get_recent_snapshots(circuit_id, 2h)

        alt menos de 2 snapshots en la ventana
            Note over P: historial insuficiente, se omite este ciclo
        else historial suficiente
            P->>DA: execute(current + historial 2h)
            DA->>DB: guarda AnomalyInference
            DA-->>P: is_anomaly, score
            alt session_id no es None
                P->>Pub: publish_anomaly_result()
                Pub->>BE: POST /notifications (type=anomaly)
            else session_id es None
                Note over P: se guarda la inferencia, pero no se notifica\n(no hay sesión activa a la que asociarla)
            end
        end
    end
```

Puntos clave de este flujo:

- **Conexión propia**: usa un servidor/credenciales de RabbitMQ independientes del resto (`MQTT_SENSOR_RABBITMQ_URL`), configurables por variable de entorno.
- **Estado en memoria por circuito**: `InMemoryCircuitSensorStateRepository` mantiene (a) el último valor conocido de cada sensor y (b) una ventana deslizante de snapshots ya armados (últimas 2h, anclada al timestamp del snapshot más reciente, no al reloj de pared). Es estado de un solo proceso — si el servicio se reinicia o se escala a varias réplicas, la ventana se reconstruye desde cero / queda fragmentada entre réplicas (ver nota de escalabilidad en `docs/architecture.md`).
- **Solo anomalías**: este flujo no hace predicción de eficiencia — para eso sigue siendo necesario el flujo de la sección 3.
- **Coexistencia con el flujo viejo**: mientras el backend siga disparando también el flujo de la sección 3 (que igualmente corre `DetectAnomaly`), pueden generarse inferencias de anomalía duplicadas para un mismo circuito/sesión. Ver nota operativa en `docs/architecture.md`.

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