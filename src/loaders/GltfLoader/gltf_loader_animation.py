from animation.bone import Bone
from animation.keyframe import Keyframe
from pyrr import quaternion as q, Quaternion, Vector3, Matrix44
import numpy as np
from pygltflib import *
from loaders.GltfLoader.gltf_loader_helpers import *

def build_rest_matrix(node):
    matrix = Matrix44(np.identity(4, dtype=np.float32))

    if node.translation is not None:
        translation = Matrix44.from_translation(node.translation)
        matrix = matrix * translation

    if node.rotation is not None:
        rotation =  Matrix44.from_quaternion(node.rotation)
        matrix = matrix * rotation

    if node.scale is not None:
        scale =  Matrix44.from_scale(node.scale)
        matrix = matrix *  scale

    return matrix

def get_inv_bind(gltf, skin):
    inverse_bind_matrices_accessor = gltf.accessors[skin.inverseBindMatrices]
    inverse_bind_matrices = get_accessor_data(gltf, inverse_bind_matrices_accessor, 'f4')
    inverse_bind_matrices = inverse_bind_matrices.reshape(-1, 4, 4)

    return {joint: inverse_bind_matrix for joint, inverse_bind_matrix in zip(skin.joints, inverse_bind_matrices)}

def find_root_node( gltf, skin):
    def traverse_node_hierarchy(node_id, skin_joints, parent_transform=None):
        node = gltf.nodes[node_id]
        if node.name == "Armature":
            print(node.rotation)
        current_transform = node.matrix if node.matrix is not None else build_rest_matrix(node)

        # Multiply by the parent's transform if it exists
        # if parent_transform is not None:
        #     current_transform = parent_transform * node_transform
        # else:
        #     current_transform = node_transform

        if node_id in skin_joints:
            return node_id, parent_transform

        if node.children:
            for child_id in node.children:
                found_node_id, transform = traverse_node_hierarchy(child_id, skin_joints, current_transform)
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

def get_bones( gltf, skin):
    def build_bone_hierarchy(gltf, node_id, inv_binds, bone_dict):
        node = gltf.nodes[node_id]
        inverse_bind_matrix = inv_binds.get(node_id, None)
        rest_transform = node.matrix if node.matrix is not None else build_rest_matrix(node)

        children_bones = []

        if node.children is not None:
            for id in node.children:
                child_bone = build_bone_hierarchy(gltf, id, inv_binds, bone_dict)
                children_bones.append(child_bone)

        bone = Bone(name=node.name, inverse_bind_matrix=inverse_bind_matrix, rest_transform=rest_transform, children=children_bones)
        bone_dict[node.name] = bone
        return bone

    root_node, transform = find_root_node(gltf, skin)
    inv_binds = get_inv_bind(gltf, skin)
    root_bone = None
    bone_dict = {}

    if(root_node is not None ):
        root_bone = build_bone_hierarchy(gltf, root_node, inv_binds, bone_dict)
        root_bone.rest_transform = transform * root_bone.rest_transform
        
    return root_bone, bone_dict

def get_channels(gltf, i, bone_dict):
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

        if path == "rotation":
            keyframes = [Keyframe(timestamp[0], Quaternion(value)) for timestamp, value in zip(input_data, output_data)]
        elif path in ["translation", "scale"]:
            keyframes = [Keyframe(timestamp[0], Vector3(value)) for timestamp, value in zip(input_data, output_data)]

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