from render.model import Model
from render.lines import Lines
from scenes.scene import Scene
from pyrr import quaternion as q, Matrix44, Vector3, Vector4
from light import Light
import imgui
from animation.bone import Bone

from typing import List, Optional, Tuple


def get_bone_connections(bone: Bone, parent_position: Optional[Matrix44] = None) -> List[Tuple[Matrix44, Matrix44]]:
    bone_connections = []

    if bone.rest_transform is not None:
        bone_position = bone.local_transform[:-1, 3]

        if parent_position is not None:
            bone_connections.append((parent_position, bone_position))

        if bone.children:
            for child in bone.children:
                bone_connections.extend(get_bone_connections(child, bone_position))

    return bone_connections


class BasicScene(Scene):
    show_model_selection = False
    show_skeleton = True
    show_model = True
    thickness_value = 1

    def load(self, model_name: str) -> None:
        self.add_entity(Model(self.app, model_name))
        self.bones = self.entities[0].get_bones()

        bone_lines = get_bone_connections(self.bones)
        self.lines = Lines(self.app, lineWidth=1, lines=bone_lines)

        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'),
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.timestamp = 0

    def unload(self) -> None:
        self.entities.clear()

    def update(self, dt: float) -> None:
        self.timestamp += dt
        self.entities[0].set_pose(self.timestamp)
        bone_lines = get_bone_connections(self.bones)
        self.lines.update(bone_lines)

        # speed = 0.5
        # angle = dt * speed
        # rotation =q.cross(self.entities[0].rotation, q.create_from_y_rotation(angle)) 
        # self.entities[0].rotation = rotation
        # self.lines.rotation = rotation

    def render_ui(self) -> None:
        imgui.new_frame()

        # Add an ImGui window
        imgui.begin("Settings")

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        # Add a slider for line thickness
        thickness_min = 1
        thickness_max = 15

        _, self.lines.lineWidth = imgui.slider_float("Line Thickness", self.thickness_value, thickness_min, thickness_max)
        self.thickness_value = self.lines.lineWidth

        _, self.show_skeleton = imgui.checkbox("Skeleton", self.show_skeleton)
        _, self.show_model = imgui.checkbox("Model", self.show_model)

        if imgui.button("Select Model"):
            if self.show_model_selection:
                self.show_model_selection = False
            else:
                self.show_model_selection = True

        # Select model button
        if self.show_model_selection:
            imgui.set_next_window_size(150, 180)
            button_pos = imgui.get_item_rect_max()
            imgui.set_next_window_position(button_pos.x - 100, button_pos.y)
            _, window_is_open = imgui.begin("Select Model", closable=True)

            if not window_is_open:
                self.show_model_selection = False

            imgui.text("Select a model")

            if imgui.button('Clown'):
                self.unload()
                self.load('Clown')
                self.show_model_selection = False
            if imgui.button('Goblin'):
                self.unload()
                self.load('Goblin')
                self.show_model_selection = False
            if imgui.button('Lady'):
                self.unload()
                self.load('Lady')
                self.show_model_selection = False
            if imgui.button('Mouse'):
                self.unload()
                self.load('Mouse')
                self.show_model_selection = False
            if imgui.button('Vampire'):
                self.unload()
                self.load('Vampire')
                self.show_model_selection = False
            imgui.end()

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def render(self) -> None:
        if self.show_model:
            for entity in self.entities:
                entity.draw(
                    self.app.camera.projection.matrix,
                    self.app.camera.matrix,
                    self.light
                )

        self.render_ui()
        if self.show_skeleton:
            self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)
