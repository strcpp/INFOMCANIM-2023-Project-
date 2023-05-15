from pyrr import Vector3


class Keyframe:
    def __init__(self, timestamp: float, value: Vector3) -> None:
        self.timestamp = timestamp
        self.value = value
