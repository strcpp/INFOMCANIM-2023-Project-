import numpy as np


class Keyframe:
    """
    Implements a Keyframe for a given timestamp and vector or quaternion
    """
    def __init__(self, timestamp: float, value: np.ndarray) -> None:
        """
        Constructor
        :param timestamp: Timestamp of the Keyframe
        :param value: Vector (translation or scale) or quaternion (rotation) of the Keyframe
        """
        self.timestamp = timestamp
        self.value = value
