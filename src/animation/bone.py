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

        if self.scales is not None and self.rotations is not None and self.translations is not None:
            if interpolation_method == "linear":
                index = binary_search_keyframe(timestamp, self.translations)

                translation_k1 = self.translations[index]
                rotation_k1 = self.rotations[index]
                scale_k1 = self.scales[index]
                translation_k2 = self.translations[index + 1]
                rotation_k2 = self.rotations[index + 1]
                scale_k2 = self.scales[index + 1]

                # translation_k1 = self.translations[translation_index]
                # translation_k2 = self.translations[translation_index + 1]

                inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp,
                                         translation_k1.timestamp, translation_k2.timestamp)

                # rotation_k1 = self.rotations[rotation_index]
                # rotation_k2 = self.rotations[rotation_index + 1]

                inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp, rotation_k1.timestamp,
                                       rotation_k2.timestamp)

                # scale_k1 = self.scales[scale_index]
                # scale_k2 = self.scales[scale_index + 1]

                inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp, scale_k1.timestamp, scale_k2.timestamp)

                from_translation(inter_translation, translation)
                from_quaternion(inter_rotation, rotation)
                from_scale(inter_scale, scale)

                self.local_transform = translation @ rotation @ scale
                self.local_transform = parent_world_transform @ self.local_transform

                for child in self.children:
                    child.set_pose(timestamp, interpolation_method, self.local_transform)

            elif interpolation_method == "hermite":
                coeff_array = np.array([[2.0, -2.0, 1.0, 1.0],
                                        [-3.0, 3.0, -2.0, -1.0],
                                        [0.0, 0.0, 1.0, 0.0],
                                        [1.0, 0.0, 0.0, 0.0]])

                index = binary_search_keyframe(timestamp, self.translations)

                translation_p0 = self.translations[index]
                rotation_p0 = self.rotations[index]
                scale_p0 = self.scales[index]
                translation_p1 = self.translations[index + 1]
                rotation_p1 = self.rotations[index + 1]
                scale_p1 = self.scales[index + 1]

                tangent_translation = np.array([0, 0, 0])

                translation_middle_1 = translation_p0.value * 0.67 + translation_p1.value * 0.33
                translation_middle_2 = translation_p0.value * 0.34 + translation_p1.value * 0.66

                tangent_translation_1 = ((translation_middle_1 - translation_p0.value) +
                                         (translation_middle_2 - translation_middle_1)) / 2

                tangent_translation_2 = ((translation_middle_2 - translation_middle_1) +
                                         (translation_p1.value - translation_middle_2)) / 2

                timestamp_norm = (timestamp - translation_p0.timestamp) / (translation_p1.timestamp -
                                                                           translation_p0.timestamp)
                timestamp_norm = clip(timestamp_norm, 0.0, 1.0)

                hermite_array = np.array([translation_p0.value - translation_p0.value,
                                          translation_p1.value - translation_p0.value,
                                          tangent_translation_1,
                                          tangent_translation_2])

                inter_translation = np.array([timestamp_norm ** 3,
                                              timestamp_norm ** 2,
                                              timestamp_norm, 1.0]) @ coeff_array @ hermite_array + translation_p0.value

                tangent_rotation = np.array([0, 0, 0, 0])

                rotation_middle_1 = rotation_p0.value * 0.67 + rotation_p1.value * 0.33
                rotation_middle_2 = rotation_p0.value * 0.34 + rotation_p1.value * 0.66

                from scipy.spatial.transform import Rotation

                r0 = rotation_p0.value / np.linalg.norm(rotation_p0.value)
                r1 = rotation_middle_1 / np.linalg.norm(rotation_middle_1)
                r2 = rotation_middle_2 / np.linalg.norm(rotation_middle_2)
                r3 = rotation_p1.value / np.linalg.norm(rotation_p1.value)

                r1_sub_r0 = Rotation.from_quat(r1).inv() * Rotation.from_quat(r0)
                angle = 2 * np.arccos(np.abs(r1_sub_r0.as_quat()[0]))
                axis = r1_sub_r0.as_quat()[1:] / np.linalg.norm(r1_sub_r0.as_quat()[1:])
                r1_sub_r0 = angle * axis

                r2_sub_r1 = Rotation.from_quat(r2).inv() * Rotation.from_quat(r1)
                angle = 2 * np.arccos(np.abs(r2_sub_r1.as_quat()[0]))
                axis = r2_sub_r1.as_quat()[1:] / np.linalg.norm(r2_sub_r1.as_quat()[1:])
                r2_sub_r1 = angle * axis

                r3_sub_r2 = Rotation.from_quat(r3).inv() * Rotation.from_quat(r2)
                angle = 2 * np.arccos(np.abs(r3_sub_r2.as_quat()[0]))
                axis = r3_sub_r2.as_quat()[1:] / np.linalg.norm(r3_sub_r2.as_quat()[1:])
                r3_sub_r2 = angle * axis

                tangent_rotation_1 = (r1_sub_r0 + r2_sub_r1) / 2
                tangent_rotation_2 = (r2_sub_r1 + r3_sub_r2) / 2

                r0_sub_r0 = Rotation.from_quat(r0).inv() * Rotation.from_quat(r0)
                angle = 2 * np.arccos(np.abs(r0_sub_r0.as_quat()[0]))
                axis = r0_sub_r0.as_quat()[1:] / np.linalg.norm(r0_sub_r0.as_quat()[1:])
                r0_sub_r0 = angle * axis

                r3_sub_r0 = Rotation.from_quat(r3).inv() * Rotation.from_quat(r0)
                angle = 2 * np.arccos(np.abs(r3_sub_r0.as_quat()[0]))
                axis = r3_sub_r0.as_quat()[1:] / np.linalg.norm(r3_sub_r0.as_quat()[1:])
                r3_sub_r0 = angle * axis

                hermite_array = np.array([r0_sub_r0,
                                          r3_sub_r0,
                                          tangent_rotation_1,
                                          tangent_rotation_2])

                inter_rotation = np.array([timestamp_norm ** 3,
                                           timestamp_norm ** 2,
                                           timestamp_norm, 1.0]) @ coeff_array @ hermite_array + r0_sub_r0

                inter_rotation = Rotation.as_quat(Rotation.from_rotvec(inter_rotation))

                tangent_scale = np.array([0, 0, 0])

                scale_middle_1 = scale_p0.value * 0.67 + scale_p1.value * 0.33
                scale_middle_2 = scale_p0.value * 0.34 + scale_p1.value * 0.66

                tangent_scale_1 = ((scale_middle_1 - scale_p0.value) +
                                   (scale_middle_2 - scale_middle_1)) / 2

                tangent_scale_2 = ((scale_middle_2 - scale_middle_1) +
                                   (scale_p1.value - scale_middle_2)) / 2

                hermite_array = np.array([scale_p0.value - scale_p0.value,
                                          scale_p1.value - scale_p0.value,
                                          tangent_scale_1,
                                          tangent_scale_2])

                inter_scale = np.array([timestamp_norm ** 3,
                                        timestamp_norm ** 2,
                                        timestamp_norm, 1.0]) @ coeff_array @ hermite_array + scale_p0.value

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
