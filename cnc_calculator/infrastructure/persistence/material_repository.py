from typing import Dict, Tuple
from cnc_calculator.domain.models.material import Material

class MaterialRepository:
    def __init__(self):
        self.materials = {
            "Soft plastics": Material(
                name="Soft plastics",
                chiploads={
                    1.5: (0.05, 0.075),
                    3.175: (0.05, 0.13),
                    6: (0.05, 0.254)
                },
                plunge_rate_range=(0.4, 0.5)
            ),
            "Soft wood & hard plastics": Material(
                name="Soft wood & hard plastics",
                chiploads={
                    1.5: (0.025, 0.04),
                    3.175: (0.025, 0.063),
                    6: (0.025, 0.127)
                },
                plunge_rate_range=(0.3, 0.3)
            ),
            "Hard wood & aluminium": Material(
                name="Hard wood & aluminium",
                chiploads={
                    1.5: (0.013, 0.013),
                    3.175: (0.013, 0.025),
                    6: (0.025, 0.05)
                },
                plunge_rate_range=(0.1, 0.3)
            )
        }

    def get_material(self, name: str) -> Material:
        return self.materials.get(name)
