from pyrr import Matrix44
from animation.bone import Bone
from typing import Optional
import numpy as np


class Animation:
    """
    Represents an animation.
    """
    def __init__(self, name: str, duration: float, root_bone: Bone, root_transform: Matrix44) -> None:
        """
        Constructor.
        :param name: Animation name.
        :param duration: Animation duration.
        :param root_bone: Animation root bone.
        :param root_transform: Animation root transform.
        """
        self.name = name
        self.duration = duration
        self.root_bone = root_bone
        self.root_transform = root_transform

    def set_pose(self, timestamp: float, interpolation_method: str, n_keyframes: int) -> None:
        """
        Sets the pose of a model based on the animation.
        :param timestamp: Current timestamp.
        :param interpolation_method: Interpolation method ('linear' or 'hermite').
        :param n_keyframes: Number of equidistant Keyframes to use for the interpolation.
        """
        t = timestamp % self.duration
        self.root_bone.set_pose(t, interpolation_method, n_keyframes, self.root_transform, True)

    def get_sorted_joints(self):
        """
        Returns a sorted list of the skeleton's joints.
        :return: Sorted list of skeleton joints.
        """
        nodes = [(self.root_bone, self.root_transform)]
        joints = []

        while len(nodes) > 0:
            current_node, parent_transform = nodes.pop()
            if current_node.index > -1:
                joint_matrix = np.transpose(current_node.inverse_bind_matrix)
                joint_matrix = current_node.local_transform @ joint_matrix
                joint_matrix = np.transpose(joint_matrix)

                pair = (current_node.index, joint_matrix)
                joints.append(pair)

                nodes.extend(
                    [(child, joint_matrix) for child in current_node.children]
                )

        joints = [x[1] for x in sorted(joints, key=lambda x: x[0])]
        return np.array(joints, dtype='f4')

    def assert_channels_not_empty(self, bone: Optional[Bone] = None) -> None:
        """
        Ensures that the animation data is loaded correctly.
        :param bone: Input Bone.
        """
        if bone is None:
            bone = self.root_bone

        if not bone.rotations:
            raise ValueError("Rotations channel is empty in bone: {}".format(bone.name))
        if not bone.scales:
            raise ValueError("Scales channel is empty in bone: {}".format(bone.name))
        if not bone.translations:
            raise ValueError("Translations channel is empty in bone: {}".format(bone.name))

        if bone.children:
            for child_bone in bone.children:
                self.assert_channels_not_empty(child_bone)

        animation = Animation(name="my_animation", duration=5.0, root_bone=root_bone, root_transform=root_transform)
        animation.assert_channels_not_empty()
        