from cnc_calculator.application.use_cases.calculate_feedrate import CalculateFeedrateUseCase
from cnc_calculator.application.use_cases.maximize_feedrate import MaximizeFeedrateUseCase
from cnc_calculator.application.use_cases.calculate_guidelines import CalculateGuidelinesUseCase
from cnc_calculator.domain.models.cutting_parameters import CuttingParameters
from cnc_calculator.domain.models.material import Material
from cnc_calculator.domain.models.cutting_style import CuttingStyle
from cnc_calculator.domain.value_objects.measurements import RPM, Feedrate, Distance
from cnc_calculator.infrastructure.persistence.material_repository import MaterialRepository
from cnc_calculator.infrastructure.persistence.cutting_style_repository import CuttingStyleRepository
from typing import Dict, Any

class CNCCalculatorViewModel:
    def __init__(self):
        self.material_repository = MaterialRepository()
        self.cutting_style_repository = CuttingStyleRepository()
        self.parameters = CuttingParameters(
            flutes=1,
            tool_diameter=6.35,
            rpm=RPM(18250),
            woc=Distance(6.35),
            doc=Distance(0.254),
            material=self.material_repository.get_material("Soft plastics"),
            cutting_style=self.cutting_style_repository.get_cutting_style("Wide and Shallow")
        )

    def update_parameter(self, parameter: str, value: Any):
        if parameter == 'flutes':
            self.parameters.flutes = int(value)
        elif parameter == 'tool_diameter':
            self.parameters.tool_diameter = float(value)
        elif parameter == 'rpm':
            self.parameters.rpm = RPM(float(value))
        elif parameter == 'woc':
            self.parameters.woc = Distance(float(value))
        elif parameter == 'doc':
            self.parameters.doc = Distance(float(value))
        elif parameter == 'material':
            self.parameters.material = self.material_repository.get_material(value)
        elif parameter == 'cutting_style':
            self.parameters.cutting_style = self.cutting_style_repository.get_cutting_style(value)
        elif parameter == 'chipload':
            self.parameters.chipload = float(value)

    def calculate_results(self) -> Dict[str, Any]:
        feedrate_use_case = CalculateFeedrateUseCase(self.parameters)
        guidelines_use_case = CalculateGuidelinesUseCase(self.parameters)

        feedrate = feedrate_use_case.execute()
        woc_range, doc_range, plunge_rate = guidelines_use_case.execute()

        return {
            'feedrate': feedrate,
            'woc_range': woc_range,
            'doc_range': doc_range,
            'plunge_rate': plunge_rate,
            'warning': feedrate > 6000
        }

    def maximize_feedrate(self, max_feedrate: float, chipload_increment: float) -> Dict[str, Any]:
        maximize_feedrate_use_case = MaximizeFeedrateUseCase(self.parameters)
        max_feedrate, max_chipload = maximize_feedrate_use_case.execute(max_feedrate, chipload_increment)

        return {
            'max_feedrate': max_feedrate,
            'max_chipload': max_chipload
        }
