from pyrr import quaternion as q, Matrix44, Vector3, Vector4
import numpy as np
from typing import List, Optional
from animation.keyframe import Keyframe
from maths import *

from pyrr import Quaternion
from dual_quaternions import DualQuaternion
from pyquaternion import Quaternion as Q

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
                 scales: Optional[Keyframe] = None, index: Optional[int] = -1) -> None:
        self.dq_bind = DualQuaternion.identity()
        self.dq = DualQuaternion.identity()
        self.name = name
        self.local_transform = local_transform if local_transform is not None else rest_transform
        self.rest_transform = rest_transform
        self.inverse_bind_matrix = inverse_bind_matrix
        self.children = children
        self.rotations = rotations
        self.translations = translations
        self.scales = scales
        self.index = index

        if inverse_bind_matrix is None:
            inverse_bind_matrix = Matrix44.identity()

        bind_mat = np.linalg.inv(np.transpose(inverse_bind_matrix))

        _, r, t = Matrix44(bind_mat).decompose()
        dq = DualQuaternion.from_quat_pose_array(np.array([r[3], r[0], r[1], r[2], t[0], t[1], t[2]]))

        self.bind_quat = dq



    def set_pose(self, timestamp: float, interpolation_method: str, parent_world_transform: Matrix44 = Matrix44(np.identity(4, dtype=np.float32)) , parent_dq: DualQuaternion = DualQuaternion(Q(0.7071067094802856, 0.7071068286895752,0,0), Q(0,0,0,0)), parent_bind: DualQuaternion = DualQuaternion.identity()) -> None:
        if self.rotations is not None and self.translations is not None and self.scales is not None:
            translation_index = binary_search_keyframe(timestamp, self.translations)
            rotation_index = binary_search_keyframe(timestamp, self.rotations)
            scale_index = binary_search_keyframe(timestamp, self.scales)

            if interpolation_method == "linear":
                translation_k1 = self.translations[translation_index]
                translation_k2 = self.translations[translation_index + 1]
                inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp,
                                          translation_k1.timestamp, translation_k2.timestamp)

                rotation_k1 = self.rotations[rotation_index]
                rotation_k2 = self.rotations[rotation_index + 1]
                inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp,
                                        rotation_k1.timestamp, rotation_k2.timestamp)

                r = inter_rotation
                t = inter_translation

                self.dq = parent_dq * DualQuaternion.from_quat_pose_array(np.array([r[3], r[0], r[1], r[2], t[0], t[1], t[2]]))
                self.dq_bind = self.bind_quat *  parent_bind


                scale_k1 = self.scales[scale_index]
                scale_k2 = self.scales[scale_index + 1]
                inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp,
                                      scale_k1.timestamp, scale_k2.timestamp)

            elif interpolation_method == "hermite":
                translation_p0 = self.translations[translation_index]
                translation_v0 = np.array([0, 0, 0])
                translation_p1 = self.translations[translation_index + 1]
                translation_v1 = np.array([0, 0, 0])
                timestamp_norm = (timestamp - translation_p0.timestamp) / (translation_p1.timestamp - translation_p0.timestamp)
                hermite_array = np.array([translation_p0.value, translation_p1.value, translation_v0, translation_v1])
                inter_translation = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

                rotation_p0 = self.rotations[rotation_index]
                rotation_v0 = np.array([0, 0, 0, 0])
                rotation_p1 = self.rotations[rotation_index + 1]
                rotation_v1 = np.array([0, 0, 0, 0])
                hermite_array = np.array([rotation_p0.value, rotation_p1.value, rotation_v0, rotation_v1])
                inter_rotation = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

                scale_p0 = self.scales[scale_index]
                scale_v0 = np.array([0, 0, 0])
                scale_p1 = self.scales[scale_index + 1]
                scale_v1 = np.array([0, 0, 0])
                hermite_array = np.array([scale_p0.value, scale_p1.value, scale_v0, scale_v1])
                inter_scale = np.array([timestamp_norm ** 3, timestamp_norm ** 2, timestamp_norm, 1]) @ coeff_array @ hermite_array

            else:
                raise ValueError("Invalid interpolation method: {}".format(interpolation_method))

            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, interpolation_method, self.local_transform, self.dq, self.dq_bind)

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.inverse_bind_matrix)
