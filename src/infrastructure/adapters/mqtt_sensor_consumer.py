from __future__ import annotations

import asyncio
import json
import logging

import aio_pika
from pydantic import ValidationError

from src.application.use_cases.realtime.process_mqtt_sensor_reading import (
    ProcessMqttSensorReading,
)
from src.domain.dtos.mqtt_sensor_message_dto import MqttSensorMessageDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# sensor_type (tal como lo publica el bridge MQTT, coincide con
# SensorType del dominio) -> campo de SensorSnapshotDTO que usa el
# modelo de anomalías. Sensores no listados aquí (ej. "density", "rpm")
# se ignoran en este flujo -- no los usa ExtractAnomalyFeatures.
_SENSOR_TYPE_TO_FIELD = {
    "ph": "ph",
    "temperature": "temperature_c",
    "turbidity": "turbidity",
    "conductivity": "conductivity",
    "alcohol": "alcohol_percent",
}


def _parse_routing_key(routing_key: str) -> tuple[int | None, str | None]:
    """
    Los ESP32 publican en el topic MQTT 'sensors/{circuit_id}/{sensor_type}',
    que RabbitMQ entrega como routing key 'sensors.{circuit_id}.{sensor_type}'
    (el plugin MQTT convierte '/' en '.'). El topic es la fuente CONFIABLE de
    circuit_id/sensor_type: ambos firmwares lo incluyen ahí, aunque el motor
    (MOTOR.ino) no los ponga en el payload JSON.

    Devuelve (circuit_id, sensor_type) o (None, None) si el routing key no
    tiene el formato esperado.
    """
    parts = routing_key.split(".")
    if len(parts) == 3 and parts[0] == "sensors":
        try:
            return int(parts[1]), parts[2]
        except ValueError:
            return None, None
    return None, None


class MqttSensorConsumer:
    """
    Adapter: consume mensajes crudos de mqtt.sensor.data.queue (un
    sensor_type + value por mensaje, publicados por el bridge MQTT ->
    RabbitMQ) y dispara ProcessMqttSensorReading por cada lectura válida.

    Conexión INDEPENDIENTE de RabbitMQConsumer (que sigue escuchando
    RABBITMQ_QUEUE con el RealtimeReadingDTO ya armado por el backend,
    para el flujo de predicción de eficiencia): tienen servidor/
    credenciales y formato de mensaje propios.
    """

    def __init__(self, process_reading: ProcessMqttSensorReading) -> None:
        self._process_reading = process_reading
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.mqtt_sensor_rabbitmq_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=20)
        queue = await channel.get_queue(settings.mqtt_sensor_queue, ensure=True)
        await queue.consume(self._handle_message)
        logger.info("MqttSensorConsumer escuchando en queue: %s", settings.mqtt_sensor_queue)

    async def stop(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("MqttSensorConsumer detenido.")

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body)

                # circuit_id/sensor_type van SIEMPRE en el topic MQTT
                # ('sensors/{circuit_id}/{sensor_type}'). Se toman de ahí
                # cuando el payload no los trae (ej. mensajes del motor,
                # MOTOR.ino, que solo publican 'value').
                circuit_id, sensor_type = _parse_routing_key(message.routing_key)
                if circuit_id is not None:
                    payload.setdefault("circuit_id", circuit_id)
                if sensor_type is not None:
                    payload.setdefault("sensor_type", sensor_type)

                try:
                    reading = MqttSensorMessageDTO(**payload)
                except ValidationError as exc:
                    # Ni el payload ni el routing key ('%s') traen los campos
                    # obligatorios: no es una lectura de sensor enrutable. Se
                    # descarta sin traceback (no es un error del consumer).
                    logger.warning(
                        "Mensaje descartado (routing_key=%s, falta %s): %s",
                        message.routing_key,
                        "; ".join(e["loc"][0] for e in exc.errors()),
                        message.body,
                    )
                    return

                if not reading.active:
                    logger.debug(
                        "circuit_id=%s: sensor '%s' inactivo, se descarta la lectura.",
                        reading.circuit_id,
                        reading.sensor_type,
                    )
                    return

                field = _SENSOR_TYPE_TO_FIELD.get(reading.sensor_type)
                if field is None:
                    # Sensor que no usa el modelo de anomalías (ej. density, rpm).
                    return

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._process_reading.execute,
                    reading.circuit_id,
                    reading.session_id,
                    reading.timestamp,
                    field,
                    reading.value,
                )
            except Exception:
                logger.exception(
                    "Error procesando mensaje de mqtt.sensor.data.queue: %s", message.body
                )