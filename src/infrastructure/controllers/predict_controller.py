from src.application.use_cases.realtime.predict_efficiency import PredictEfficiency
from src.domain.dtos.efficiency_response_dto import EfficiencyResponseDTO
from src.domain.dtos.sensor_window_dto import SensorWindowDTO


class PredictController:
    """
    Controller: orquesta la petición HTTP de predicción de eficiencia
    hacia el use case correspondiente. No contiene lógica de negocio,
    solo traduce DTO de entrada -> use case -> DTO de salida.
    """

    def __init__(self, predict_efficiency: PredictEfficiency) -> None:
        self._predict_efficiency = predict_efficiency

    def handle(self, window: SensorWindowDTO) -> EfficiencyResponseDTO:
        efficiency = self._predict_efficiency.execute(window)
        return EfficiencyResponseDTO(efficiency_percent=efficiency)