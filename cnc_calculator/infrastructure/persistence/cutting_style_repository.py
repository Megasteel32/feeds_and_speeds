from cnc_calculator.domain.models.cutting_style import CuttingStyle

class CuttingStyleRepository:
    def __init__(self):
        self.cutting_styles = {
            "Wide and Shallow": CuttingStyle(
                name="Wide and Shallow",
                woc_multiplier=(0.4, 1.0),
                doc_multiplier=(0.05, 0.1)
            ),
            "Narrow and Deep": CuttingStyle(
                name="Narrow and Deep",
                woc_multiplier=(0.1, 0.25),
                doc_multiplier=(1.0, 3.0)
            )
        }

    def get_cutting_style(self, name: str) -> CuttingStyle:
        return self.cutting_styles.get(name)
