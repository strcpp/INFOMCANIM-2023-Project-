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

    def set_pose(self, timestamp: float, interpolation_method: str,
                 parent_world_transform: Matrix44 = Matrix44(np.identity(4, dtype=np.float32))) -> None:
        if interpolation_method == "linear":
            translation_index = binary_search_keyframe(timestamp, self.translations)
            rotation_index = binary_search_keyframe(timestamp, self.rotations)
            scale_index = binary_search_keyframe(timestamp, self.scales)

            # Currently only uses the first keyframe
            # Should be linearly/cubicly be interpolated between *_index and *_index + 1
            translation_k1 = self.translations[0]
            translation_k2 = self.translations[-1]

            inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp, translation_k1.timestamp,
                                     translation_k2.timestamp)

            rotation_k1 = self.rotations[rotation_index]
            rotation_k2 = self.rotations[rotation_index + 1]

            inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp, rotation_k1.timestamp,
                                   rotation_k2.timestamp)

            scale_k1 = self.scales[0]
            scale_k2 = self.scales[-1]

            inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp, scale_k1.timestamp, scale_k2.timestamp)

            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, interpolation_method, self.local_transform)
        elif interpolation_method == "hermite":
            coeff_array = np.array([[2, -2, 1, 1], [-3, 3, -2, -1], [0, 0, 1, 0], [1, 0, 0, 0]])

            translation_p0 = self.translations[0]
            translation_v0 = np.array([0, 0, 0])
            translation_p1 = self.translations[-1]
            translation_v1 = np.array([0, 0, 0])

            timestamp_norm = (timestamp - translation_p0.timestamp) / (translation_p1.timestamp - translation_p0.timestamp)

            hermite_array = np.array([translation_p0.value, translation_p1.value, translation_v0, translation_v1])
            inter_translation = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

            rotation_p0 = self.rotations[0]
            rotation_v0 = np.array([0, 0, 0, 0])
            rotation_p1 = self.rotations[-1]
            rotation_v1 = np.array([0, 0, 0, 0])

            hermite_array = np.array([rotation_p0.value, rotation_p1.value, rotation_v0, rotation_v1])
            inter_rotation = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

            scale_p0 = self.scales[0]
            scale_v0 = np.array([0, 0, 0])
            scale_p1 = self.scales[-1]
            scale_v1 = np.array([0, 0, 0])

            hermite_array = np.array([scale_p0.value, scale_p1.value, scale_v0, scale_v1])
            inter_scale = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, interpolation_method, self.local_transform)

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.inverse_bind_matrix)
