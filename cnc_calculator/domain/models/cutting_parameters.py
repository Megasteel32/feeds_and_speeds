from typing import Optional
from .material import Material
from .cutting_style import CuttingStyle
from ..value_objects.measurements import Distance
import math

class CuttingParameters:
    def __init__(self, flutes: int, tool_diameter: Distance, rpm: int, woc: Distance, doc: Distance, material: Material, cutting_style: CuttingStyle, chipload: Optional[float] = None):
        self.flutes = flutes
        self.tool_diameter = tool_diameter
        self.rpm = rpm
        self.woc = woc
        self.doc = doc
        self.material = material
        self.cutting_style = cutting_style
        self.chipload = chipload

    def calculate_feedrate(self) -> float:
        base_feedrate = self.rpm.value * self.chipload * self.flutes
        if self.woc.value > self.tool_diameter.value / 2:
            return base_feedrate
        return base_feedrate / math.sqrt(1 - (1 - 2 * self.woc.value / self.tool_diameter.value) ** 2)

    @property
    def feedrate(self) -> float:
        return self.calculate_feedrate()
