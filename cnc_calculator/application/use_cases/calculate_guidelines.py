from cnc_calculator.domain.models.cutting_parameters import CuttingParameters
from cnc_calculator.domain.services.cutting_guidelines_service import CuttingGuidelinesService

class CalculateGuidelinesUseCase:
    def __init__(self, parameters: CuttingParameters):
        self.parameters = parameters

    def execute(self):
        service = CuttingGuidelinesService(self.parameters)
        return service.calculate_guidelines()
