from render.mesh import Mesh
from pyrr import Quaternion, Vector3, Matrix44
import numpy as np
from typing import Optional
from animation.bone import Bone
from light import Light
from animation.animation import Animation

# Define MAX_BONES
MAX_BONES = 100


def copy_bones(bone: Bone) -> Bone:
    """
    Copies parent bone to the children bone.
    :param bone: Parent bone
    :return: Copied bone
    """
    copied_children = []
    for child in bone.children:
        copied_children.append(copy_bones(child))
    copied_bone = Bone(bone.name, bone.inverse_bind_matrix, bone.rest_transform, copied_children, bone.local_transform,
                       bone.rotations, bone.translations, bone.scales, bone.index)
    return copied_bone


class Model:
    """
    Represents a 3D model.
    """

    def __init__(self, app, mesh_name: str) -> None:
        """
        Constructor.
        :param app: Glw app.
        :param mesh_name: Name of the model's mesh.
        """

        self.current_animation = None
        self.animation_length = None
        self.current_animation_id = None
        meshes = Mesh.instance()
        self.app = app
        self.commands = meshes.data[mesh_name][0]
        self.animations = []
        for animation in meshes.data[mesh_name][1]:
            self.animations.append(Animation(animation.name, animation.duration, copy_bones(animation.root_bone),
                                             animation.root_transform))

        self.set_animation_id(0)

        # Check if the skeleton is properly connected
        if self.animations[0]:
            if self.animations[0].root_bone is None:
                raise ValueError("The root bone of the skeleton is not set.")
        else:
            raise ValueError("No animation data is available.")

        self.translation = Vector3()
        self.rotation = Quaternion()
        self.scale = Vector3([1.0, 1.0, 1.0])

        self.timestamp = 0
        self.animation_speed = 1
        self.show_model = True
        self.show_skeleton = True

        self.model_transformation = Matrix44.identity()

        self.n_keyframes = self.get_number_of_keyframes()
        self.max_keyframes = self.get_number_of_keyframes()

    def update(self, dt: float, interpolation_method: str):
        """
        Updates the model's pose.
        :param dt: Current timestamp
        :param interpolation_method: Interpolation method (can be 'linear' or 'hermite').
        """
        self.timestamp += dt * self.animation_speed
        # Check if the animation reached the end
        if self.timestamp >= self.animation_length:
            self.timestamp = 0.0
        # Check if the animation reached the beginning
        elif self.timestamp < 0:
            self.timestamp = self.animation_length
 
        self.current_animation.set_pose(self.timestamp, interpolation_method, self.get_number_of_keyframes())

    def move(self, dx: float, dz: float):
        self.translation += Vector3([dx, 0, dz])
        self.calculate_model_matrix()

    def rotate_y(self, d: float):
        self.rotation = Quaternion.from_y_rotation(d) * self.rotation
        self.calculate_model_matrix()

    def set_animation_id(self, animation_id: int) -> None:
        """
        Sets the current animation, its id and its length.
        :param animation_id: Current animation id.
        """
        if animation_id >= len(self.animations):
            return

        self.current_animation_id = animation_id
        self.current_animation = self.animations[animation_id]
        self.animation_length = self.get_animation_length()

    def get_animation_length(self) -> float:
        """
        Retrieves the animation duration from the loaded animation data.
        :return: Duration of the animation.
        """
        if self.current_animation:
            return self.current_animation.duration
        return 0.0

    def get_root_bone(self) -> Optional[Bone]:
        """
        Returns the current animation's root bone.
        :return: Root bone of the current animation.
        """
        if self.current_animation:
            return self.current_animation.root_bone
        return None

    def get_number_of_keyframes(self) -> int:
        """
        Returns the total number of Keyframes of the current animation.
        :return: Total number of Keyframes of the current animation.
        """
        if self.current_animation:
            return self.current_animation.root_bone.get_number_of_keyframes()
        return 0

    def calculate_model_matrix(self):
        trans = Matrix44.from_translation(self.translation)
        rot = Matrix44.from_quaternion(Quaternion(self.rotation))
        scale = Matrix44.from_scale(self.scale)
        self.model_transformation = trans * rot * scale

    def get_model_matrix(self, transformation_matrix: Optional[Matrix44] = None) -> np.ndarray:
        """
        Returns the matrix of the model.
        :param transformation_matrix: Transformation matrix of the model.
        :return: Model matrix.
        """
        model = self.model_transformation
        if transformation_matrix is not None:
            model = self.model_transformation * transformation_matrix

        return np.array(model, dtype='f4')

    def draw(self, proj_matrix: Matrix44, view_matrix: Matrix44, light: Light) -> None:
        """
        Draws a 3D model.
        :param proj_matrix: Projection matrix.
        :param view_matrix: View matrix.
        :param light: Scene light.
        """
        for i, command in enumerate(self.commands):
            transformation_matrix, prog, texture, vao = command[3], command[2], command[1], command[0]

            prog['light.Ia'].write(light.Ia)
            prog['light.Id'].write(light.Id)
            prog['light.Is'].write(light.Is)
            prog['light.position'].write(light.position)
            prog['camPos'].write(np.array(self.app.camera.position, dtype='f4'))

            prog['model'].write(self.get_model_matrix(transformation_matrix))
            prog['view'].write(view_matrix)
            prog['projection'].write(proj_matrix)
            prog['useTexture'].value = texture is not None

            if self.current_animation:
                joints_mats = self.current_animation.get_sorted_joints()
                prog['numBones'].value = len(joints_mats)  # Pass the number of bones to the shader
                prog['numBoneInfluences'].value = min(len(joints_mats), MAX_BONES)  # Limit number of bone influences
                prog['jointsMatrices'].write(joints_mats.tobytes())

            if texture is not None:
                texture.use()

            vao.render()
