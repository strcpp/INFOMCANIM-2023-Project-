from animation.bone import Bone
from typing import List, Optional, Tuple
from pyrr import Matrix44


def get_bone_connections(bone: Bone, parent_position: Optional[Matrix44] = None) -> List[Tuple[Matrix44, Matrix44]]:
    """
    Gets a list of bones that are connected to a given bone.
    :param bone: Given Bone object.
    :param parent_position: Position of the parent bone.
    :return: List of bone connections for a given bone.
    """
    bone_connections = []

    if bone.local_transform is not None:
        bone_position = bone.local_transform[:-1, 3]

        if parent_position is not None:
            bone_connections.append((parent_position, bone_position))

        if bone.children:
            for child in bone.children:
                bone_connections.extend(get_bone_connections(child, bone_position))

    return bone_connections
