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
    animation_speed = 1
    default_speed = False
    previous_animation_speed = animation_speed

    def load(self) -> None:
        self.models = ['Vampire', 'Lady']

        for model in self.models:
            self.add_entity(model, Model(self.app, model))

        self.current_model = 'Vampire'

        self.bones = self.find(self.current_model).get_bones()

        self.lines = Lines(self.app, lineWidth=1)
        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'),
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.timestamp = 0

    def unload(self) -> None:
        self.entities.clear()

    def update(self, dt: float) -> None:
        model = self.find(self.current_model)
        self.timestamp += dt * self.animation_speed
        
        #Check if the animation reached end
        if self.timestamp >= model.animation_length:
            self.timestamp = 0.0
        
        model.set_pose(self.timestamp)
        
        self.find(self.current_model).set_pose(self.timestamp)
        bone_lines = get_bone_connections(
            self.find(self.current_model).get_bones()
        )

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

        _, self.lines.lineWidth = imgui.slider_float("Line Thickness", self.thickness_value, thickness_min,
                                                     thickness_max)
        self.thickness_value = self.lines.lineWidth

        _, self.show_skeleton = imgui.checkbox("Skeleton", self.show_skeleton)
        _, self.show_model = imgui.checkbox("Model", self.show_model)

        imgui.text("Select a model")

        _, selected_model = imgui.combo('##model_combo', self.models.index(self.current_model), self.models)

        if selected_model != -1:
            selected_model_name = self.models[selected_model]
            if selected_model_name != self.current_model:
                self.current_model = selected_model_name

        _, self.animation_speed = imgui.slider_float("Animation speed", self.animation_speed, -2, 2)

         # Add a slider for animation length
        animation_length = self.find(self.current_model).animation_length
        _, self.timestamp = imgui.slider_float("Animation Length", self.timestamp, 0, animation_length)


        # Add Play/Stop button
        if self.animation_speed == 0:
            button_label = "Play"
        else:
            button_label = "Stop"

        if imgui.button(button_label):
            if self.animation_speed == 0:
                self.animation_speed = self.previous_animation_speed
            else:
                self.previous_animation_speed = self.animation_speed
                self.animation_speed = 0
        imgui.same_line()

        # Play animation forwards
        if imgui.button("Forward"):
            self.animation_speed = 1
        imgui.same_line()

        # Play animation backwards
        if imgui.button("Backward"):
            self.animation_speed = -1

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def render(self) -> None:
        if self.show_model:
            self.find(self.current_model).draw(
                self.app.camera.projection.matrix,
                self.app.camera.matrix,
                self.light
            )

        self.render_ui()
        if self.show_skeleton:
            self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)
