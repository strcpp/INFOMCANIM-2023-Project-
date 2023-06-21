from render.model import Model
from render.lines import Lines
from render.grid import Grid
from render.skybox import Skybox
from scenes.scene import Scene
from pyrr import Vector3
from light import Light
import imgui
from animation.bone import Bone
from animation.get_bone_connections import get_bone_connections
import numpy as np

class MultipleModelsScene(Scene):
    """
    Implements the scene of the application.
    """
    show_model_selection = False
    show_skeleton = True
    show_model = True
    thickness_value = 1
    animation_speed = 1
    default_speed = False
    interpolation_method = "linear"
    n_keyframes = 2
    max_keyframes = 2
    models = []
    current_model = ""
    lines = None
    light = None
    skybox = None
    timestamp = 0
    grid = None

    current_model_to_add = 0

    def load(self) -> None:
        """
        Load method.
        """
        self.model_names = ['Batman', 'Joker']

        self.lines = Lines(self.app, lineWidth=1)
        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'),
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.skybox = Skybox(self.app, skybox='clouds', ext='png')

        self.grid = Grid(self.app, color=[0.9, 0.9, 0.9], size=500)

        self.timestamp = 0

    def unload(self) -> None:
        """
        Unload method.
        """
        self.entities.clear()

    def update(self, dt: float) -> None:
        """
        Update method.
        :param dt: Update time step.
        """
        for model_name in self.model_names_in_scene:
            model = self.find(model_name)
            model.update(dt, self.interpolation_method)

    def render_ui(self) -> None:
        """
        Renders the UI.
        """
        imgui.new_frame()

        # Change the style of the entire ImGui interface
        imgui.style_colors_classic()

        # Add an ImGui window
        imgui.begin("Settings", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
        
        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        _, self.current_model_to_add = imgui.combo("##model_combo", self.current_model_to_add, self.model_names)
        if imgui.button("Add Model"):
            model_name = self.add_model(self.model_names[self.current_model_to_add])
            self.set_model(model_name)

        # Add a collapsible header for Model Settings
        if imgui.tree_node("Model Selection") and len(self.model_names_in_scene) > 0:
            _, selected_model = imgui.combo('##model_combo', self.model_names_in_scene.index(self.current_model), self.model_names_in_scene)
            if selected_model != -1:
                selected_model_name = self.model_names_in_scene[selected_model]
                if selected_model_name != self.current_model:
                    self.set_model(selected_model_name)
            imgui.tree_pop()

        # Add a collapsible header for Line Settings
        if imgui.tree_node("Skeleton Settings"):
            # Add a slider for line thickness
            thickness_min = 1
            thickness_max = 15
            _, self.lines.lineWidth = imgui.slider_float("Line Thickness", self.thickness_value, thickness_min,
                                                         thickness_max)
            self.thickness_value = self.lines.lineWidth

            _, self.show_skeleton = imgui.checkbox("Skeleton", self.show_skeleton)
            _, self.show_model = imgui.checkbox("Model", self.show_model)
            imgui.tree_pop()

        # Add a collapsible header for Animation Settings
        if imgui.tree_node("Animation Settings"):
            imgui.text("Select an animation")
            _, selected_animation = imgui.combo("##animation_combo", self.current_model_entity.current_animation_id,
                                                self.current_animation_names)
            if selected_animation != -1 and selected_animation != self.current_model_entity.current_animation_id:
                self.current_model_entity.timestamp = 0
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
            _, self.current_model_entity.animation_speed = imgui.slider_float("Animation Speed", self.current_model_entity.animation_speed, min_speed, max_speed)
            imgui.pop_style_color()

            _, self.n_keyframes = imgui.slider_int("Keyframes to Use", self.n_keyframes, 2, self.max_keyframes)
            imgui.tree_pop()

        # Add a collapsible header for Playback Controls
        if imgui.tree_node("Playback Controls"):
            animation_length = self.current_model_entity.animation_length
            length_color = np.interp(self.current_model_entity.timestamp, [0, animation_length], [0, 1])
            red_2 = length_color
            green_2 = 0.0
            blue_2 = 1.0 - length_color
            slider_color = (red_2, green_2, blue_2, 1.0)  # Ranging from dark blue to bright orange
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, *slider_color)
            _, self.current_model_entity.timestamp = imgui.slider_float("Animation Length", self.current_model_entity.timestamp, 0, animation_length)
            imgui.pop_style_color()

            if self.current_model_entity.animation_speed != 0:
                play_stop_button_label = "Stop"
                play_stop_button_color = (0.694, 0.282, 0.282, 1.0)  # Red color for Stop button
            else:
                play_stop_button_label = "Play"
                play_stop_button_color = (0.282, 0.361, 0.306, 1.0)  # Green color for Play button

            imgui.push_style_color(imgui.COLOR_BUTTON, *play_stop_button_color)
            if imgui.button(play_stop_button_label):
                if self.current_model_entity.animation_speed == 0:
                    self.current_model_entity.animation_speed = 1.0
                else:
                    self.current_model_entity.animation_speed = 0.0
            imgui.pop_style_color()
            imgui.tree_pop()

            default_button_color = (0.694, 0.282, 0.282, 1.0)
            active_button_color = (0.282, 0.361, 0.306, 1.0)

            
            imgui.same_line()  # Add this line to align the buttons in a row

            # Forward button
            if self.current_model_entity.animation_speed != 1:
                forward_button_color = default_button_color
            else:
                forward_button_color = active_button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *forward_button_color)
            if imgui.button("Forward"):
                if self.current_model_entity.animation_speed != 1:
                    self.current_model_entity.animation_speed = 1

            imgui.pop_style_color()

            imgui.same_line()  # Add this line to align the buttons in a row

            # Backward button
            if self.current_model_entity.animation_speed != -1:
                backward_button_color = default_button_color
            else:
                backward_button_color = active_button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *backward_button_color)
            if imgui.button("Backward"):
                if self.current_model_entity.animation_speed != -1:
                    self.current_model_entity.animation_speed = -1

            imgui.pop_style_color()

            imgui.same_line()  # Add this line to align the buttons in a row

            # Linear button
            if self.interpolation_method != "linear":
                linear_button_color = default_button_color
            else:
                linear_button_color = active_button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *linear_button_color)
            if imgui.button("Linear"):
                self.interpolation_method = "linear"
            imgui.pop_style_color()

            imgui.same_line()  # Add this line to align the buttons in a row

            # Hermite button
            if self.interpolation_method != "hermite":
                hermite_button_color = default_button_color
            else:
                hermite_button_color = active_button_color

            imgui.push_style_color(imgui.COLOR_BUTTON, *hermite_button_color)
            if imgui.button("Hermite"):
                self.interpolation_method = "hermite"
            imgui.pop_style_color()

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())


    def render(self) -> None:
        """
        Renders all objects in the scene.
        """
        self.skybox.draw(self.app.camera.projection.matrix, self.app.camera.matrix)

        for model_name in self.model_names_in_scene:
            model = self.find(model_name)
            if self.show_model:
                model.draw(
                    self.app.camera.projection.matrix,
                    self.app.camera.matrix,
                    self.light
                )
                
            if self.show_skeleton:
                bone_lines = get_bone_connections(model.get_root_bone())
                self.lines.update(bone_lines)
                self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)

        self.grid.draw(self.app.camera.projection.matrix, self.app.camera, self.timestamp)

        self.render_ui()