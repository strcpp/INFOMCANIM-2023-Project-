from render.mesh import Mesh
from pyrr import Quaternion, Vector3, Matrix44
import numpy as np
from typing import Optional
from animation.bone import Bone
from light import Light

# Define MAX_BONES
MAX_BONES = 100


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
        self.animations = meshes.data[mesh_name][1]
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

    def set_pose(self, timestamp: float, interpolation_method: str, n_keyframes: int) -> None:
        """
        Sets the pose of the model.
        :param timestamp: Current timestamp.
        :param interpolation_method: Interpolation method ('linear' or 'hermite').
        :param n_keyframes: Number of equidistant Keyframes to use for the interpolation.
        """
        self.current_animation.set_pose(timestamp, interpolation_method, n_keyframes)

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

    def get_model_matrix(self, transformation_matrix: Optional[Matrix44]) -> np.ndarray:
        """
        Returns the matrix of the model.
        :param transformation_matrix: Transformation matrix of the model.
        :return: Model matrix.
        """
        trans = Matrix44.from_translation(self.translation)
        rot = Matrix44.from_quaternion(Quaternion(self.rotation))
        scale = Matrix44.from_scale(self.scale)
        model = trans * rot * scale

        if transformation_matrix is not None:
            model = model * transformation_matrix

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
