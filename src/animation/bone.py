from pyrr import quaternion as q, Matrix44, Vector3, Vector4
import numpy as np
from typing import List, Optional
from animation.keyframe import Keyframe
from maths import *

#preallocate matrices
translation = np.identity(4)
rotation = np.identity(4)
scale = np.identity(4)

def binary_search_keyframe(timestamp: float, channel: List[Keyframe]) -> int:
    # Find keyframes for given timestamp
    low = 0
    high = len(channel)

    while low <= high:
        mid = (high + low) // 2
        if timestamp > channel[mid].timestamp:
            low = mid + 1
        elif timestamp < channel[mid].timestamp:
            high = mid - 1

    return high


class Bone:
    def __init__(self, name: str, inverse_bind_matrix: np.ndarray, rest_transform: Matrix44,
                 children: List['Bone'] = None, local_transform: Optional[Matrix44] = None,
                 rotations: Optional[Keyframe] = None, translations: Optional[Keyframe] = None,
                 scales: Optional[Keyframe] = None) -> None:
        self.name = name
        # The current local transformation matrix
        self.local_transform = local_transform if local_transform is not None else rest_transform
        # Transformation of the bone at the start of the animation, a matrix, might not be necessary
        self.rest_transform = rest_transform
        # The joint offset translation matrix, this determines the pivot point relative to its parent
        self.inverse_bind_matrix = inverse_bind_matrix

        self.children = children

        # animation channels, each channel contains a list of a Keyframes
        # rotations -> Keyframe: time, Quaternion 
        # scale, translation -> Keyframe: time, Vector3
        self.rotations = rotations
        self.translations = translations
        self.scales = scales

    def set_pose(self, timestamp: float,
                 parent_world_transform: Matrix44 = Matrix44(np.identity(4, dtype=np.float32))) -> None:
        scale_index = binary_search_keyframe(timestamp, self.scales)
        rotation_index = binary_search_keyframe(timestamp, self.rotations)
        translation_index = binary_search_keyframe(timestamp, self.translations)

        # Currently only uses the first keyframe
        # Should be linearly/cubicly be interpolated between *_index and *_index + 1
        from_translation(self.translations[translation_index].value, translation)
        from_quaternion(self.rotations[rotation_index].value, rotation)
        from_scale(self.scales[scale_index].value, scale)

        self.local_transform = translation @ rotation @ scale
        self.local_transform = parent_world_transform @ self.local_transform

        for child in self.children:
            child.set_pose(timestamp, self.local_transform)

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.inverse_bind_matrix)
