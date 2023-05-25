import numpy as np


class Keyframe:
    def __init__(self, timestamp: float, value: np.ndarray) -> None:
        self.timestamp = timestamp
        self.value = value
