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

        self.rci = 0 # rotation channel index
        self.tci = 0 # translation channel index
        self.sci = 0 # scale channel index

        self.timestamp = 0

    def update(self, dt, parent_world_m = Matrix44(np.identity(4, dtype=np.float32))):
        self.timestamp += dt
       
        if self.timestamp > self.translations[self.tci].timestamp:
            self.tci += 1
        if self.timestamp > self.rotations[self.rci].timestamp:
            self.rci += 1
        if self.timestamp > self.scales[self.sci].timestamp:
            self.sci += 1

        # Repeat animation when no keyframes are left
        # This is probably wrong, since some bones could be finished earlier than others if their channels
        # have a different number of keyframes or timing
        if self.tci >= len(self.translations) or self.rci >= len(self.rotations) or self.sci >= len(self.scales):
            self.tci = 0
            self.rci = 0
            self.sci = 0
            self.timestamp = 0

        self.current_transform = self.rest_transform

        translation = Matrix44.from_translation(self.translations[self.tci].value)
        self.current_transform = self.current_transform * translation

        rotation =  Matrix44.from_quaternion(self.rotations[self.rci].value)
        self.current_transform = self.current_transform * rotation
            
        scale =  Matrix44.from_scale(self.scales[self.sci].value)
        self.current_transform = self.current_transform * scale

        self.current_transform = parent_world_m * self.current_transform

        if (self.tci == 0):
            print(self.rest_transform)
            print(Matrix44.from_translation(self.translations[0].value))
            print(Matrix44.from_quaternion(self.rotations[0].value))
            print(Matrix44.from_scale(self.scales[0].value))

        for child in self.children:
            child.update(dt, self.current_transform)


    # gets the bind-pose (usually T-pose) world-space matrix.
    def get_global_bind_matrix(self):
        return np.linalg.inv(self.inverse_bind_matrix)