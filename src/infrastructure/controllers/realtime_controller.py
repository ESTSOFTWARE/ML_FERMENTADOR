from src.application.use_cases.realtime.process_realtime_reading import ProcessRealtimeReading
from src.domain.dtos.realtime_reading_dto import RealtimeReadingDTO


class RealtimeController:
    """
    Controller: orquesta la petición HTTP que el backend dispara cada
    vez que llega una lectura nueva de sensores para una sesión activa,
    hacia el use case orquestador process_realtime_reading.
    """

    def __init__(self, process_realtime_reading: ProcessRealtimeReading) -> None:
        self._process_reading = process_realtime_reading

    def handle(self, reading: RealtimeReadingDTO) -> dict:
        return self._process_reading.execute(reading)