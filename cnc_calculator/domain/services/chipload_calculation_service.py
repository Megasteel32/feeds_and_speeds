from typing import Dict, Tuple
from ..models.material import Material

class ChiploadCalculationService:
    def __init__(self, material: Material):
        self.material = material
        self.tool_diameter = None

    def suggest_chipload(self, tool_diameter: float) -> Tuple[float, float]:
        self.tool_diameter = tool_diameter
        chipload_data = self.material.chiploads
        diameters = sorted(chipload_data.keys())

        if tool_diameter <= diameters[0]:
            return chipload_data[diameters[0]]
        if tool_diameter >= diameters[-1]:
            return self._extrapolate_chipload(chipload_data, diameters[-2:])

        for i in range(len(diameters) - 1):
            if diameters[i] <= tool_diameter <= diameters[i + 1]:
                return self._interpolate(
                    tool_diameter,
                    diameters[i], chipload_data[diameters[i]],
                    diameters[i + 1], chipload_data[diameters[i + 1]]
                )

        return chipload_data[diameters[0]]  # fallback

    def _interpolate(self, x, x1, y1, x2, y2):
        """Linear interpolation helper"""
        if isinstance(y1, tuple) and isinstance(y2, tuple):
            return (
                y1[0] + (x - x1) * (y2[0] - y1[0]) / (x2 - x1),
                y1[1] + (x - x1) * (y2[1] - y1[1]) / (x2 - x1)
            )
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

    def _extrapolate_chipload(self, chipload_data, last_two_diameters):
        """Extrapolate chipload for larger tool diameters"""
        d1, d2 = last_two_diameters
        v1, v2 = chipload_data[d1], chipload_data[d2]

        return self._interpolate(
            self.tool_diameter,
            d1, v1,
            d2, v2
        )
