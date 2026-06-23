from src.application.use_cases.inference.get_inference_history import GetInferenceHistory


class InferenceController:
    """
    Controller: orquesta las consultas de historial de inferencias
    hacia el use case correspondiente.
    """

    def __init__(self, get_inference_history: GetInferenceHistory) -> None:
        self._use_case = get_inference_history

    def get_all(self, limit: int = 100) -> list[dict]:
        inferences = self._use_case.get_all(limit=limit)
        return [i.to_dict() for i in inferences]

    def get_by_session(self, session_id: int) -> list[dict]:
        inferences = self._use_case.get_by_session(session_id)
        return [i.to_dict() for i in inferences]

    def get_anomalies_only(self, limit: int = 100) -> list[dict]:
        inferences = self._use_case.get_anomalies_only(limit=limit)
        return [i.to_dict() for i in inferences]