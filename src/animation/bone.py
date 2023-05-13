from pyrr import quaternion as q, Matrix44, Vector3, Vector4
import numpy as np

class Bone:
    def __init__(self,name, inverse_bind_matrix, rest_transform, children=None, local_transform=None, rotations = None, translations = None, scales= None):
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

    def set_pose(self, timestamp, parent_world_transform = Matrix44(np.identity(4, dtype=np.float32))):
        scale_index = self.binary_search_keyframe(timestamp, self.scales)
        rotation_index = self.binary_search_keyframe(timestamp, self.rotations)
        translation_index = self.binary_search_keyframe(timestamp, self.translations)
        
        # Currently only uses the first keyframe
        # Should be linearly/cubicly be interpolated between *_index and *_index + 1
        scale =  Matrix44.from_scale(self.scales[scale_index].value)
        rotation =  Matrix44.from_quaternion(self.rotations[rotation_index].value)
        translation = Matrix44.from_translation(self.translations[translation_index].value).transpose()

        self.local_transform = scale * rotation * translation
        self.local_transform = self.local_transform * parent_world_transform

        for child in self.children:
            child.set_pose(timestamp, self.local_transform)

    def binary_search_keyframe(self, timestamp, channel):
        # Find keyframes for given timestamp
        low = 0
        high = len(channel)
        mid = 0

        while low <= high:
            mid = (high + low) // 2
            if timestamp > channel[mid].timestamp:
                low = mid + 1
            elif timestamp < channel[mid].timestamp:
                high = mid - 1
        
        return high

    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self):
        return np.linalg.inv(self.inverse_bind_matrix)