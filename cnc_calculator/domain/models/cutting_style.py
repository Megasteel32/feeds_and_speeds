class CuttingStyle:
    def __init__(self, name: str, woc_multiplier: tuple[float, float], doc_multiplier: tuple[float, float]):
        self.name = name
        self.woc_multiplier = woc_multiplier
        self.doc_multiplier = doc_multiplier
