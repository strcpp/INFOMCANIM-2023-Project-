from pyrr import Matrix44
import numpy as np
from typing import List, Optional
from animation.keyframe import Keyframe
from maths import *
from numba import njit

# preallocate matrices
translation = np.identity(4)
rotation = np.identity(4)
scale = np.identity(4)


@njit(cache=True)
def binary_search_keyframe(timestamp: float, timestamps: np.ndarray) -> int:
    """
    Finds the closest smallest Keyframe of a given timestamp.
    :param timestamp: Current timestamp.
    :param timestamps: List of timestamps for all Keyframes.
    :return: Index of the closest smallest Keyframe of a given timestamp.
    """
    # Find keyframes for given timestamp
    low = 0
    high = len(timestamps)

    while low <= high:
        mid = (high + low) // 2
        if timestamp > timestamps[mid]:
            low = mid + 1
        elif timestamp < timestamps[mid]:
            high = mid - 1

    return high


class Bone:
    """
    Implements each bone of the model.
    """
    timestamp_norm = 0
    index = 0
    indices = None
    left_index = 0
    right_index = 0
    i0 = 0
    i1 = 0
    i2 = 0
    i3 = 0
    timestamp_0 = 0
    timestamp_1 = 0
    timestamp_2 = 0
    timestamp_3 = 0

    def __init__(self, name: str, inverse_bind_matrix: np.ndarray, rest_transform: Matrix44,
                 children: List['Bone'] = None, local_transform: Optional[Matrix44] = None,
                 rotations: Optional[Keyframe] = None, translations: Optional[Keyframe] = None,
                 scales: Optional[Keyframe] = None, index: Optional[int] = -1) -> None:
        """
        Constructor.
        :param name: Name of the bone.
        :param inverse_bind_matrix: Inverse bind matrix of the bone.
        :param rest_transform: Rest transform of the bone.
        :param children: Children bones of the bone.
        :param local_transform: Local transform of the bone.
        :param rotations: Rotation quaternions of the bone for each Keyframe.
        :param translations: Translation vectors of the bone for each Keyframe.
        :param scales: Scale vectors of the bone for each Keyframe.
        :param index: Index of the bone in the list of joints.
        """
        self.name = name
        self.local_transform = local_transform if local_transform is not None else rest_transform
        self.rest_transform = rest_transform
        self.inverse_bind_matrix = inverse_bind_matrix
        self.children = children
        self.rotations = rotations
        self.translations = translations
        self.scales = scales
        self.index = index

    def set_pose(self, timestamp: float, interpolation_method: str, n_keyframes: int,
                 parent_world_transform: Matrix44 = Matrix44(np.identity(4, dtype=np.float32)),
                 is_parent: bool = False) -> None:
        """
        Performs linear or hermite curve interpolation on a given Keyframe in order to animate the model.
        :param timestamp: Current timestamp.
        :param interpolation_method: Interpolation method (can be 'linear' or 'hermite').
        :param n_keyframes: The number of equidistant keyframes that will be taken into account during interpolation.
        :param parent_world_transform: World transformation matrix of the parent Bone.
        :param is_parent: Is True if the current Bone is the parent Bone.
        """
        if self.scales is not None and self.rotations is not None and self.translations is not None:
            if is_parent:
                Bone.index = binary_search_keyframe(timestamp,
                                                    np.array([keyframe.timestamp for keyframe in self.translations]))
                Bone.indices = np.linspace(0, len(self.translations) - 1, n_keyframes, dtype=int)

                if interpolation_method == "linear":
                    Bone.left_index = np.searchsorted(Bone.indices, Bone.index, side='right') - 1
                    if Bone.left_index < 0:
                        Bone.left_index = 0
                    Bone.right_index = Bone.left_index + 1
                elif interpolation_method == "hermite":
                    Bone.i1 = np.searchsorted(Bone.indices, Bone.index, side='right') - 1
                    Bone.i0 = Bone.i1 - 1
                    if Bone.i0 < 0:
                        Bone.i0 = 0
                    Bone.i2 = Bone.i1 + 1
                    Bone.i3 = Bone.i2 + 1

                    if Bone.i3 > n_keyframes - 1:
                        Bone.i3 = n_keyframes - 1

                    Bone.timestamp_0 = self.translations[Bone.indices[Bone.i0]].timestamp
                    Bone.timestamp_1 = self.translations[Bone.indices[Bone.i1]].timestamp
                    Bone.timestamp_2 = self.translations[Bone.indices[Bone.i2]].timestamp
                    Bone.timestamp_3 = self.translations[Bone.indices[Bone.i3]].timestamp
                    Bone.timestamp_norm = (timestamp - Bone.timestamp_1) / (Bone.timestamp_2 - Bone.timestamp_1)
            if interpolation_method == "linear":
                translation_k1 = self.translations[Bone.indices[Bone.left_index]]
                translation_k2 = self.translations[Bone.indices[Bone.right_index]]

                rotation_k1 = self.rotations[Bone.indices[Bone.left_index]]
                rotation_k2 = self.rotations[Bone.indices[Bone.right_index]]

                scale_k1 = self.scales[Bone.indices[Bone.left_index]]
                scale_k2 = self.scales[Bone.indices[Bone.right_index]]

                inter_translation = lerp(translation_k1.value, translation_k2.value, timestamp,
                                         translation_k1.timestamp, translation_k2.timestamp)

                inter_rotation = slerp(rotation_k1.value, rotation_k2.value, timestamp, rotation_k1.timestamp,
                                       rotation_k2.timestamp)

                inter_scale = lerp(scale_k1.value, scale_k2.value, timestamp, scale_k1.timestamp, scale_k2.timestamp)
            elif interpolation_method == "hermite":
                translation_k0 = self.translations[Bone.indices[Bone.i0]].value
                translation_k1 = self.translations[Bone.indices[Bone.i1]].value
                translation_k2 = self.translations[Bone.indices[Bone.i2]].value
                translation_k3 = self.translations[Bone.indices[Bone.i3]].value

                rotation_k0 = self.rotations[Bone.indices[Bone.i0]].value
                rotation_k1 = self.rotations[Bone.indices[Bone.i1]].value
                rotation_k2 = self.rotations[Bone.indices[Bone.i2]].value
                rotation_k3 = self.rotations[Bone.indices[Bone.i3]].value

                scale_k0 = self.scales[Bone.indices[Bone.i0]].value
                scale_k1 = self.scales[Bone.indices[Bone.i1]].value
                scale_k2 = self.scales[Bone.indices[Bone.i2]].value
                scale_k3 = self.scales[Bone.indices[Bone.i3]].value

                translation_tangent_v0 = calculate_translation_tangent(translation_k0, translation_k2,
                                                                       Bone.timestamp_2, Bone.timestamp_0)
                translation_tangent_v1 = calculate_translation_tangent(translation_k1, translation_k3,
                                                                       Bone.timestamp_3, Bone.timestamp_1)

                inter_translation = hermite_translation(translation_k1, translation_k2,
                                                        translation_tangent_v0, translation_tangent_v1,
                                                        Bone.timestamp_norm)

                rotation_tangent_v0 = calculate_rotation_tangent(rotation_k0, rotation_k2,
                                                                 Bone.timestamp_2, Bone.timestamp_0)

                rotation_tangent_v1 = calculate_rotation_tangent(rotation_k1, rotation_k3,
                                                                 Bone.timestamp_3, Bone.timestamp_1)

                inter_rotation = hermite_rotation(rotation_k1, rotation_k2,
                                                  rotation_tangent_v0, rotation_tangent_v1, Bone.timestamp_norm)

                scale_tangent_v0 = calculate_scale_tangent(scale_k0, scale_k2, Bone.timestamp_2, Bone.timestamp_0)
                scale_tangent_v1 = calculate_scale_tangent(scale_k1, scale_k3, Bone.timestamp_3, Bone.timestamp_1)

                inter_scale = hermite_scale(scale_k1, scale_k2, scale_tangent_v0, scale_tangent_v1, Bone.timestamp_norm)

            else:
                raise ValueError("Invalid interpolation method: {}".format(interpolation_method))
            from_translation(inter_translation, translation)
            from_quaternion(inter_rotation, rotation)
            from_scale(inter_scale, scale)

            self.local_transform = translation @ rotation @ scale
            self.local_transform = parent_world_transform @ self.local_transform

            for child in self.children:
                child.set_pose(timestamp, interpolation_method, n_keyframes, self.local_transform, False)

    @njit(cache=True)
    def get_global_bind_matrix(self) -> np.ndarray:
        """
        Gets the bind-pose (usually T-pose) world-space matrix.
        :return: bind-pose world-space matrix.
        """
        return np.linalg.inv(self.inverse_bind_matrix)

    def get_number_of_keyframes(self) -> int:
        """
        Gets the number of keyframes for the current animation.
        :return: Number of keyframes for the current animation.
        """
        return len(self.translations)
