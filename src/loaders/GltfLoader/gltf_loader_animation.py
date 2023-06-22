from animation.bone import Bone
from animation.keyframe import Keyframe
from pyrr import Matrix44
import numpy as np
from pygltflib import *
from loaders.GltfLoader.gltf_loader_helpers import *


def build_rest_matrix(node):
    """

    :param node:
    :return:
    """
    matrix = Matrix44(np.identity(4, dtype=np.float32))

    if node.scale is not None:
        scale = Matrix44.from_scale(node.scale)
        matrix = matrix * scale

    if node.rotation is not None:
        rotation = Matrix44.from_quaternion(node.rotation)
        matrix = matrix * rotation

    if node.translation is not None:
        translation = Matrix44.from_translation(node.translation).transpose()
        matrix = matrix * translation

    return matrix


def get_inv_bind(gltf, skin):
    """

    :param gltf:
    :param skin:
    :return:
    """
    inverse_bind_matrices_accessor = gltf.accessors[skin.inverseBindMatrices]
    inverse_bind_matrices = get_accessor_data(gltf, inverse_bind_matrices_accessor, 'f4')
    inverse_bind_matrices = inverse_bind_matrices.reshape(-1, 4, 4)

    return {joint: inverse_bind_matrix for joint, inverse_bind_matrix in zip(skin.joints, inverse_bind_matrices)}


def find_root_node(gltf, skin):
    """

    :param gltf:
    :param skin:
    :return:
    """
    def traverse_node_hierarchy(node_id, skin_joints, parent_transform=None):
        """

        :param node_id:
        :param skin_joints:
        :param parent_transform:
        :return:
        """
        node = gltf.nodes[node_id]
        local_transform = node.matrix if node.matrix is not None else build_rest_matrix(node)

        if node_id in skin_joints:
            return node_id, parent_transform

        if node.children:
            for child_id in node.children:
                found_node_id, transform = traverse_node_hierarchy(child_id, skin_joints, local_transform)
                if found_node_id is not None:
                    return found_node_id, transform

        return None, None

    skin_joints = set(skin.joints)

    for scene in gltf.scenes:
        for node_id in scene.nodes:
            found_node_id, accumulated_transform = traverse_node_hierarchy(node_id, skin_joints)
            if found_node_id is not None:
                return found_node_id, accumulated_transform

    return None, None


def get_bones(gltf: GLTF2, skin: Skin) -> Tuple[Bone, Matrix44, Dict[str, Bone]]:
    """

    :param gltf:
    :param skin:
    :return:
    """
    def build_bone_hierarchy(gltf: GLTF2, node_id: int, inv_binds: Dict[int, np.ndarray],
                             bone_dict: Dict[str, Bone]) -> Bone:
        """

        :param gltf:
        :param node_id:
        :param inv_binds:
        :param bone_dict:
        :return:
        """

        node = gltf.nodes[node_id]

        inverse_bind_matrix = inv_binds.get(node_id, None)
        rest_transform = node.matrix if node.matrix is not None else build_rest_matrix(node)

        children_bones = []

        if node.children is not None:
            for child_id in node.children:
                child_bone = build_bone_hierarchy(gltf, child_id, inv_binds, bone_dict)
                children_bones.append(child_bone)

        bone_index = skin.joints.index(node_id) if node_id in skin.joints else -1

        bone = Bone(name=node.name, inverse_bind_matrix=inverse_bind_matrix, rest_transform=rest_transform,
                    children=children_bones, index=bone_index)
        bone_dict[node.name] = bone
        return bone

    root_node, root_transform = find_root_node(gltf, skin)
    inv_binds = get_inv_bind(gltf, skin)
    root_bone = None
    bone_dict = {}

    if root_node is not None:
        root_bone = build_bone_hierarchy(gltf, root_node, inv_binds, bone_dict)

    return root_bone, root_transform, bone_dict


def get_animation_duration(gltf: GLTF2, i: int, bone_dict: Dict[str, Bone]) -> float:
    """
    Gets the duration of an animation of a gltf file.
    :param gltf: Gltf file.
    :param i: Animation index.
    :param bone_dict: Dictionary of Bones.
    :return: Animation duration.
    """
    animation = gltf.animations[i]
    duration = 0.0

    for channel in animation.channels:
        target_node = channel.target.node
        node_name = gltf.nodes[target_node].name
        path = channel.target.path

        sampler = animation.samplers[channel.sampler]
        input_accessor = gltf.accessors[sampler.input]
        output_accessor = gltf.accessors[sampler.output]

        input_data = get_accessor_data(gltf, input_accessor, 'f4')
        output_data = get_accessor_data(gltf, output_accessor, 'f4')

        keyframes = [Keyframe(timestamp[0], np.array(value)) for timestamp, value in zip(input_data, output_data)]

        duration = max(duration, max(input_data))

        if node_name not in bone_dict:
            continue

        bone = bone_dict[node_name]

        if path == "rotation":
            bone.rotations = keyframes
        elif path == "translation":
            bone.translations = keyframes
        elif path == "scale":
            bone.scales = keyframes

    return duration[0]
