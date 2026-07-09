import asyncio
import json
import logging

import aio_pika

from src.application.use_cases.realtime.process_realtime_reading import ProcessRealtimeReading
from src.domain.dtos.realtime_reading_dto import RealtimeReadingDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self, process_reading: ProcessRealtimeReading) -> None:
        self._process_reading = process_reading
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(settings.rabbitmq_queue, durable=True)
        await queue.consume(self._handle_message)
        logger.info("RabbitMQ consumer escuchando en queue: %s", settings.rabbitmq_queue)

    async def stop(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ consumer detenido.")

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                data = json.loads(message.body)
                reading = RealtimeReadingDTO(**data)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._process_reading.execute, reading)
            except Exception:
                logger.exception("Error procesando mensaje de RabbitMQ: %s", message.body)