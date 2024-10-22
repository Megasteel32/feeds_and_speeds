from typing import Dict, Tuple

class Material:
    def __init__(self, name: str, chiploads: Dict[float, Tuple[float, float]], plunge_rate_range: Tuple[float, float]):
        self.name = name
        self.chiploads = chiploads
        self.plunge_rate_range = plunge_rate_range
