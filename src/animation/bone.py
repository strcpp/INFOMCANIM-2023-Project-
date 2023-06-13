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

    def set_pose(self, timestamp: float, interpolation_method: str, n_keyframes: int,
                 parent_world_transform: Matrix44 = Matrix44(np.identity(4, dtype=np.float32))) -> None:

        if self.scales is not None and self.rotations is not None and self.translations is not None:
            if interpolation_method == "linear":
                index = binary_search_keyframe(timestamp, self.translations)
                indices = np.linspace(0, len(self.translations) - 1, n_keyframes, dtype=int)
                left_index = np.searchsorted(indices, index, side='right') - 1
                right_index = left_index + 1

                translation_k1 = self.translations[indices[left_index]]
                translation_k2 = self.translations[indices[right_index]]

                rotation_k1 = self.rotations[indices[left_index]]
                rotation_k2 = self.rotations[indices[right_index]]

                scale_k1 = self.scales[indices[left_index]]
                scale_k2 = self.scales[indices[right_index]]

                inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp,
                                         translation_k1.timestamp, translation_k2.timestamp)

                inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp, rotation_k1.timestamp,
                                       rotation_k2.timestamp)

                inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp, scale_k1.timestamp, scale_k2.timestamp)

            elif interpolation_method == "hermite":
                index = binary_search_keyframe(timestamp, self.translations)
                indices = np.linspace(0, len(self.translations) - 1, n_keyframes, dtype=int)
                left_index = np.searchsorted(indices, index, side='right') - 1
                right_index = left_index + 1
                
                timestamp_0 = self.translations[indices[left_index]].timestamp
                timestamp_1 = self.translations[indices[right_index]].timestamp
                timestamp_norm = (timestamp - timestamp_0) / (timestamp_1 - timestamp_0)

                translation_k0 = self.translations[indices[left_index]].value
                translation_k1 = self.translations[indices[right_index]].value

                rotation_k0 = self.rotations[indices[left_index]].value
                rotation_k1 = self.rotations[indices[right_index]].value

                scale_k0 = self.scales[indices[left_index]].value
                scale_k1 = self.scales[indices[right_index]].value

                translation_tangent = calculate_translation_tangent(translation_k0, translation_k1,
                                                                    timestamp_0, timestamp_1)

                inter_translation = hermite_translation(translation_k0, translation_k1,
                                                        translation_tangent, translation_tangent, timestamp_norm)

                rotation_tangent = calculate_rotation_tangent(rotation_k0, rotation_k1,
                                                              timestamp_0, timestamp_1)

                inter_rotation = hermite_rotation(rotation_k0, rotation_k1,
                                                  rotation_tangent, rotation_tangent, timestamp_norm)

                scale_tangent = calculate_scale_tangent(scale_k0, scale_k1, timestamp_0, timestamp_1)

                inter_scale = hermite_scale(scale_k0, scale_k1, scale_tangent, scale_tangent, timestamp_norm)
            else:
                raise ValueError("Invalid interpolation method: {}".format(interpolation_method))

            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, interpolation_method, n_keyframes, self.local_transform)

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.inverse_bind_matrix)

    def get_number_of_keyframes(self) -> int:
        return len(self.translations)
