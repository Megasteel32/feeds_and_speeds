from ..models.cutting_parameters import CuttingParameters
from ..models.cutting_style import CuttingStyle
from ..models.material import Material

class CuttingGuidelinesService:
    def __init__(self, parameters: CuttingParameters):
        self.parameters = parameters

    def calculate_guidelines(self):
        cutting_config = self.parameters.cutting_style
        material_config = self.parameters.material

        woc_range = self._calculate_range(
            self.parameters.tool_diameter,
            cutting_config.woc_multiplier
        )

        doc_range = self._calculate_range(
            self.parameters.tool_diameter,
            cutting_config.doc_multiplier
        )

        plunge_rate = self._calculate_range(
            self.parameters.feedrate,
            material_config.plunge_rate_range
        )

        return woc_range, doc_range, plunge_rate

    def _calculate_range(self, base_value, multiplier_tuple):
        return (
            base_value * multiplier_tuple[0],
            base_value * multiplier_tuple[1]
        )
