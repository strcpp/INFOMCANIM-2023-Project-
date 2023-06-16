from render.model import Model
from render.lines import Lines
from render.skybox import Skybox
from scenes.scene import Scene
from pyrr import quaternion as q, Matrix44, Vector3, Vector4
from light import Light
import imgui
from animation.bone import Bone
import numpy as np
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
    interpolation_method = "linear"
    n_keyframes = 2
    max_keyframes = 2
    models = []
    current_model = ""
    bones = None
    lines = None
    light = None
    skybox = None
    timestamp = 0

    def load(self) -> None:
        self.models = ['Batman', 'Joker']

        for model in self.models:
            self.add_entity(model, Model(self.app, model))

        self.set_model('Batman')

        self.bones = self.find(self.current_model).get_bones()

        self.lines = Lines(self.app, lineWidth=1)
        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'),
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.skybox = Skybox(self.app, skybox='clouds', ext='png')

        self.timestamp = 0

        self.n_keyframes = self.find(self.current_model).get_number_of_keyframes()
        self.max_keyframes = self.n_keyframes

    def unload(self) -> None:
        self.entities.clear()

    def update(self, dt: float) -> None:
        animation_length = self.current_model_entity.animation_length

        if self.animation_speed > 0:  # Forward animation
            self.timestamp += dt * self.animation_speed

            # Check if the animation reached the end
            if self.timestamp >= animation_length:
                self.timestamp = 0.0

        elif self.animation_speed < 0:  # Backward animation
            self.timestamp -= dt * abs(self.animation_speed)

            # Check if the animation reached the beginning
            if self.timestamp < 0:
                self.timestamp = animation_length

        self.current_model_entity.set_pose(self.timestamp, self.interpolation_method, self.n_keyframes)
        bone_lines = get_bone_connections(self.current_model_entity.get_bones())
        self.lines.update(bone_lines)

    def render_ui(self) -> None:
        imgui.new_frame()

        # Change the style of the entire ImGui interface
        imgui.style_colors_classic()

        # Add an ImGui window
        imgui.begin("Settings")

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        # Add a collapsible header for Model Settings
        if imgui.tree_node("Model Selection"):
            _, selected_model = imgui.combo('##model_combo', self.models.index(self.current_model), self.models)
            if selected_model != -1:
                selected_model_name = self.models[selected_model]
                if selected_model_name != self.current_model:
                    self.timestamp = 0
                    self.set_model(selected_model_name)
            imgui.tree_pop()

        # Add a collapsible header for Line Settings
        if imgui.tree_node("Skeleton Settings"):
            # Add a slider for line thickness
            thickness_min = 1
            thickness_max = 15
            _, self.lines.lineWidth = imgui.slider_float("Line Thickness", self.thickness_value, thickness_min, thickness_max)
            self.thickness_value = self.lines.lineWidth

            _, self.show_skeleton = imgui.checkbox("Skeleton", self.show_skeleton)
            _, self.show_model = imgui.checkbox("Model", self.show_model)
            imgui.tree_pop()

        # Add a collapsible header for Animation Settings
        if imgui.tree_node("Animation Settings"):
            imgui.text("Select an animation")
            _, selected_animation = imgui.combo("##animation_combo", self.current_model_entity.current_animation_id, self.current_animation_names)
            if selected_animation != -1 and selected_animation != self.current_model_entity.current_animation_id:
                self.timestamp = 0
                self.current_model_entity.set_animation_id(selected_animation)

            # Add a slider for animation speed
            min_speed = 0.0  # Set the minimum speed value to 0/ Animation stopped
            max_speed = 10.0  # Adjust if we want
            speed_color = np.interp(self.animation_speed, [0, max_speed], [0, 1])
            red = 1.0
            green = 1.0 - speed_color
            blue = 0.0
            slider_color = (red, green, blue, 1.0)  # Ranging from yellow to bright red
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, *slider_color)
            _, self.animation_speed = imgui.slider_float("Animation Speed", self.animation_speed, min_speed, max_speed)
            imgui.pop_style_color()

            _, self.n_keyframes = imgui.slider_int("Keyframes to Use", self.n_keyframes, 2, self.max_keyframes)
            imgui.tree_pop()

        # Add a collapsible header for Playback Controls
        if imgui.tree_node("Playback Controls"):
            animation_length = self.current_model_entity.animation_length
            length_color = np.interp(self.timestamp, [0, animation_length], [0, 1])
            red_2 = length_color
            green_2 = 0.0
            blue_2 = 1.0 - length_color
            slider_color = (red_2, green_2, blue_2, 1.0)  # Ranging from dark blue to bright orange
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, *slider_color)
            _, self.timestamp = imgui.slider_float("Animation Length", self.timestamp, 0, animation_length)
            imgui.pop_style_color()

            if self.animation_speed != 0:
                button_label = "Stop"
                button_color = (0.694, 0.282, 0.282, 1.0)  # Red color for Stop button
            else:
                button_label = "Play"
                button_color = (0.282, 0.361, 0.306, 1.0)  # Green color for Play button

            imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)
            if imgui.button(button_label):
                if self.animation_speed == 0:
                    self.animation_speed = 1.0
                else:
                    self.animation_speed = 0.0
            imgui.pop_style_color()
            imgui.tree_pop()

            forward_button_color = button_color
            if self.animation_speed == 1:
                forward_button_color = button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *forward_button_color)
            if imgui.button("Forward"):
                if self.animation_speed != 1:
                    self.animation_speed = 1
                else:
                    self.animation_speed = self.previous_animation_speed

            imgui.same_line()
            imgui.pop_style_color()

            backward_button_color = button_color
            if self.animation_speed == -1:
                backward_button_color = button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *backward_button_color)
            if imgui.button("Backward"):
                if self.animation_speed != -1:
                    self.animation_speed = -1
                else:
                    self.animation_speed = self.previous_animation_speed

            imgui.pop_style_color()

            linear_button_color = button_color
            if self.interpolation_method == "linear":
                linear_button_color = button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *linear_button_color)
            if imgui.button("Linear"):
                self.interpolation_method = "linear"

            imgui.pop_style_color()
            imgui.same_line()

            hermite_button_color = button_color
            if self.interpolation_method == "hermite":
                hermite_button_color = button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *hermite_button_color)
            if imgui.button("Hermite"):
                self.interpolation_method = "hermite"

            imgui.pop_style_color()

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def render(self) -> None:
        self.skybox.draw(self.app.camera.projection.matrix, self.app.camera.matrix)
        if self.show_model:
            self.find(self.current_model).draw(
                self.app.camera.projection.matrix,
                self.app.camera.matrix,
                self.light
            )

        self.render_ui()

        if self.show_skeleton:
            self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)
