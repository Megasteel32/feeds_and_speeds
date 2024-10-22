from pydantic import BaseModel
from typing import Dict, Tuple

class MaterialProperties(BaseModel):
    chiploads: Dict[float, Tuple[float, float]]
    plunge_rate_range: Tuple[float, float]

class MaterialConfig(BaseModel):
    materials: Dict[str, MaterialProperties]

class CuttingStyleProperties(BaseModel):
    woc_multiplier: Tuple[float, float]
    doc_multiplier: Tuple[float, float]

class CuttingStyleConfig(BaseModel):
    cutting_styles: Dict[str, CuttingStyleProperties]
