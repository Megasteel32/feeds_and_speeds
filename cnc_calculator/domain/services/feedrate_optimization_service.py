from ..models.cutting_parameters import CuttingParameters

class FeedrateOptimizationService:
    def __init__(self, parameters: CuttingParameters):
        self.parameters = parameters

    def maximize_feedrate(self, max_feedrate: float, chipload_increment: float) -> tuple[float, float]:
        tool_diameter = self.parameters.tool_diameter.value
        lower_chipload, upper_chipload = self.parameters.material.chiploads[tool_diameter]
        
        current_chipload = lower_chipload
        max_feedrate = 0
        max_chipload = current_chipload

        while abs(upper_chipload - lower_chipload) > chipload_increment:
            mid_chipload = (lower_chipload + upper_chipload) / 2
            self.parameters.chipload = mid_chipload
            feedrate = self.parameters.feedrate

            if feedrate <= max_feedrate:
                max_feedrate = feedrate
                max_chipload = mid_chipload
                lower_chipload = mid_chipload
            else:
                upper_chipload = mid_chipload

        return max_feedrate, max_chipload
