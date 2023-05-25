from pyrr import quaternion as q, Matrix44, Vector3, Vector4
import numpy as np
from typing import List, Optional
from animation.keyframe import Keyframe
from maths import *

# preallocate matrices
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

        if(self.scales is not None and self.rotations is not None and self.translations is not None):
            scale_index = binary_search_keyframe(timestamp, self.scales)
            rotation_index = binary_search_keyframe(timestamp, self.rotations)
            translation_index = binary_search_keyframe(timestamp, self.translations)

            # Currently only uses the first keyframe
            # Should be linearly/cubicly be interpolated between *_index and *_index + 1
            translation_k1 = self.translations[translation_index]
            translation_k2 = self.translations[translation_index + 1]

            inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp, translation_k1.timestamp,
                                    translation_k2.timestamp)

            rotation_k1 = self.rotations[rotation_index]
            rotation_k2 = self.rotations[rotation_index + 1]

            inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp, rotation_k1.timestamp,
                                rotation_k2.timestamp)

            scale_k1 = self.scales[scale_index]
            scale_k2 = self.scales[scale_index + 1]

            inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp, scale_k1.timestamp, scale_k2.timestamp)

            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, self.local_transform)

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.inverse_bind_matrix)
