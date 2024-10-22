from cnc_calculator.domain.services.feedrate_optimization_service import FeedrateOptimizationService
from cnc_calculator.domain.models.cutting_parameters import CuttingParameters

class MaximizeFeedrateUseCase:
    def __init__(self, parameters: CuttingParameters):
        self.parameters = parameters
        self.service = FeedrateOptimizationService(parameters)

    def execute(self, max_feedrate: float, chipload_increment: float) -> tuple[float, float]:
        return self.service.maximize_feedrate(max_feedrate, chipload_increment)
