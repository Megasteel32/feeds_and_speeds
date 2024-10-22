from cnc_calculator.domain.models.cutting_parameters import CuttingParameters
from cnc_calculator.domain.services.chipload_calculation_service import ChiploadCalculationService
from cnc_calculator.domain.services.feedrate_optimization_service import FeedrateOptimizationService

class CalculateFeedrateUseCase:
    def __init__(self, cutting_parameters: CuttingParameters):
        self.cutting_parameters = cutting_parameters
        self.chipload_service = ChiploadCalculationService(cutting_parameters.material)
        self.feedrate_service = FeedrateOptimizationService(cutting_parameters)

    def execute(self) -> float:
        suggested_chipload = self.chipload_service.suggest_chipload(self.cutting_parameters.tool_diameter)
        self.cutting_parameters.chipload = suggested_chipload[0]  # Use the lower bound of the suggested chipload range
        return self.cutting_parameters.feedrate
