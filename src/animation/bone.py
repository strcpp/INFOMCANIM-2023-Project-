from pyrr import quaternion as q, Matrix44, Vector3, Vector4
import numpy as np

class Bone:
    def __init__(self,name, inverse_bind_matrix, rest_transform, children=None, current_transform=None, rotations = None, translations = None, scales= None):
        self.name = name
        # The current local transformation matrix
        self.current_transform = current_transform if current_transform is not None else rest_transform
        # Transformation of the bone at the start of the animation, a matrix, might not be necessary
        self.rest_transform =  rest_transform
        # The joint offset translation matrix, this determines the pivot point relative to its parent
        self.inverse_bind_matrix = inverse_bind_matrix

        self.children = children

        # animation channels, each channel contains a list of a Keyframes
        # rotations -> Keyframe: time, Quaternion 
        # scale, translation -> Keyframe: time, Vector3
        self.rotations = rotations
        self.translations = translations
        self.scales = scales


    # gets the bone-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self):
        return np.linalg.inv(self.inverse_bind_matrix)