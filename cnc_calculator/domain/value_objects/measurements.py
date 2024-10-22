from typing import Any

class RPM:
    def __init__(self, value: int):
        if value <= 0:
            raise ValueError("RPM must be a positive integer")
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RPM):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        return f"RPM({self.value})"

class Feedrate:
    def __init__(self, value: float):
        if value <= 0:
            raise ValueError("Feedrate must be a positive float")
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Feedrate):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        return f"Feedrate({self.value})"

class Distance:
    def __init__(self, value: float):
        if value <= 0:
            raise ValueError("Distance must be a positive float")
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Distance):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        return f"Distance({self.value})"
