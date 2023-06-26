from render.lines import Lines
from render.grid import Grid
from render.skybox import Skybox
from scenes.scene import Scene
from pyrr import Vector3
from light import Light
import imgui
from animation.get_bone_connections import get_bone_connections
import pygame
import numpy as np
import os


class MultipleModelsScene(Scene):
    """
    Implements the scene of the application.
    """
    thickness_value = 1
    animation_speed = 1
    default_speed = False
    interpolation_method = "linear"
    n_keyframes = 2
    max_keyframes = 2
    models = []
    lines = None
    light = None
    skybox = None
    grid = None
    tracks = ["Track 1", "Track 2", "Track 3"]
    sounds = dict()
    selected_track = tracks[0]
    overall_volume = 1
    keys_pressed = []

    model_names = []
    current_animation_names = None
    current_model_entity = None
    current_model = ""

    current_model_to_add = 0

    def load(self) -> None:
        """
        Load method.
        """
        self.model_names = ['Batman', 'Joker']

        self.lines = Lines(self.app)
        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'),
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.skybox = Skybox(self.app, skybox='clouds', ext='png')

        self.grid = Grid(self.app, color=[0.9, 0.9, 0.9], size=500)

        # Load and play the MP3 file
        pygame.init()
        pygame.mixer.init()

        for track in self.tracks:
            path = os.path.join("resources/tracks", track + ".mp3")
            self.sounds[track] = pygame.mixer.Sound(path)

    def unload(self) -> None:
        """
        Unload method.
        """
        self.entities.clear()
        pygame.mixer.Channel(0).stop()

    def update(self, dt: float) -> None:
        """
        Update method.
        :param dt: Update time step.
        """
        for idx, model_name in enumerate(self.model_names_in_scene):
            model = self.find(model_name)
            model.update(dt, self.interpolation_method)

        move_speed = 0.05
        rot_speed = 0.03

        keys = self.app.wnd.keys
        for key in self.keys_pressed:
            if key == keys.W:
                self.current_model_entity.move(0, move_speed)
            elif key == keys.S:
                self.current_model_entity.move(0, -move_speed)
            elif key == keys.A:
                self.current_model_entity.move(move_speed, 0)
            elif key == keys.D:
                self.current_model_entity.move(-move_speed, 0)
            elif key == keys.Q:
                self.current_model_entity.rotate_y(rot_speed)
            elif key == keys.E:
                self.current_model_entity.rotate_y(-rot_speed)

    def key_event(self, key: int, action: str):
        """ 
        key event method. 
        """
        keys = self.app.wnd.keys
        if self.current_model_entity != None:
            if action == keys.ACTION_PRESS:
                self.keys_pressed.append(key)
            elif action == keys.ACTION_RELEASE:
                self.keys_pressed.remove(key)
        
    def render_ui(self) -> None:
        """
        Renders the UI.
        """
        imgui.new_frame()

        # Change the style of the entire ImGui interface
        imgui.style_colors_classic()

        # Add an ImGui window
        imgui.set_next_window_position(0, 20)
        imgui.set_next_window_size(370, 0)
        imgui.begin("Settings", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        imgui.new_line()
        imgui.text("Available models:")
        _, self.current_model_to_add = imgui.combo("##add_model_combo", self.current_model_to_add, self.model_names)
        imgui.same_line()
        if imgui.button("Add Model"):
            model_name = self.add_model(self.model_names[self.current_model_to_add])
            self.set_model(model_name)

        imgui.spacing()
        imgui.spacing()
        imgui.separator()
        # Add a collapsible header for Model Settings
        imgui.text("Current models in scene:")
        models_in_scene = self.model_names_in_scene
        if len(self.model_names_in_scene) == 0:
            models_in_scene = [""]
        _, selected_model = imgui.combo('##select_model_combo', models_in_scene.index(self.current_model),
                                        models_in_scene)
        if selected_model != -1 and len(self.model_names_in_scene) > 0:
            selected_model_name = self.model_names_in_scene[selected_model]
            if selected_model_name != self.current_model:
                self.set_model(selected_model_name)

        if self.current_model_entity is not None:
            imgui.same_line()
            if imgui.button("Remove model"):
                if selected_model > 0:
                    self.set_model(self.model_names_in_scene[selected_model - 1])
                elif selected_model < len(self.model_names_in_scene) - 1:
                    self.set_model(self.model_names_in_scene[selected_model + 1])
                else:
                    self.current_animation_names = None
                    self.current_model_entity = None
                    self.current_model = ""
                del self.model_names_in_scene[selected_model]

        if self.current_model_entity is not None:
            imgui.spacing()
            imgui.indent(16)
            # Add a collapsible header for Line Settings
            imgui.text("Skeleton Settings:")
            # Add a slider for line thickness
            thickness_min = 1
            thickness_max = 15
            _, self.lines.lineWidth = imgui.slider_float("Line Thickness", self.thickness_value, thickness_min,
                                                         thickness_max)
            self.thickness_value = self.lines.lineWidth

            _, self.current_model_entity.show_skeleton = imgui.checkbox("Skeleton",
                                                                        self.current_model_entity.show_skeleton)
            _, self.current_model_entity.show_model = imgui.checkbox("Model", self.current_model_entity.show_model)

            # Add a collapsible header for Animation Settings
            imgui.spacing()
            imgui.text("Animation Settings:")
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
            _, self.current_model_entity.animation_speed = imgui.slider_float("Animation Speed",
                                                                              self.current_model_entity.animation_speed,
                                                                              min_speed, max_speed)
            imgui.pop_style_color()

            _, self.current_model_entity.n_keyframes = imgui.slider_int("Keyframes to Use",
                                                                        self.current_model_entity.n_keyframes, 2,
                                                                        self.current_model_entity.max_keyframes)

            # Add a collapsible header for Playback Controls
            imgui.spacing()
            imgui.text("Playback Controls:")
            animation_length = self.current_model_entity.animation_length
            length_color = np.interp(self.current_model_entity.timestamp, [0, animation_length], [0, 1])
            red_2 = length_color
            green_2 = 0.0
            blue_2 = 1.0 - length_color
            slider_color = (red_2, green_2, blue_2, 1.0)  # Ranging from dark blue to bright orange
            imgui.push_style_color(imgui.COLOR_SLIDER_GRAB_ACTIVE, *slider_color)
            _, self.current_model_entity.timestamp = imgui.slider_float("Animation Length",
                                                                        self.current_model_entity.timestamp, 0,
                                                                        animation_length)
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

            imgui.spacing()
            imgui.text("Interpolation method:")
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

            imgui.unindent(16)

        imgui.spacing()
        imgui.separator()
        imgui.spacing()
        imgui.push_style_color(imgui.COLOR_BUTTON, *(0.282, 0.361, 0.306, 1.0))
        if imgui.button("Play all"):
            for model_name in self.model_names_in_scene:
                model = self.find(model_name)
                model.animation_speed = 1
        imgui.same_line()
        if imgui.button("Stop all"):
            for model_name in self.model_names_in_scene:
                model = self.find(model_name)
                model.animation_speed = 0
        imgui.pop_style_color()

        # Add a collapsible header for Soundtrack Settings
        imgui.spacing()
        imgui.spacing()
        imgui.separator()
        imgui.text("Soundtrack Settings")
        # Add a slider for volume
        volume_min = 0.0
        volume_max = 1.0

        _, self.overall_volume = imgui.slider_float("Volume", self.overall_volume, volume_min, volume_max)

        # Set the volume for all tracks
        for track in self.tracks:
            pygame.mixer.Channel(self.tracks.index(track)).set_volume(self.overall_volume)

        # Add a dropdown menu for track selection
        _, selected_index = imgui.combo("Track", self.tracks.index(self.selected_track), self.tracks)
        if selected_index != -1 and self.selected_track != self.tracks[selected_index]:
            self.selected_track = self.tracks[selected_index]
            pygame.mixer.Channel(0).play(self.sounds[self.selected_track])

        imgui.same_line()

        # Get the current state of the music player for the selected track
        is_playing = pygame.mixer.Channel(0).get_busy()

        # Determine the label and color for the play/stop button
        if is_playing:
            play_stop_button_label = "Stop"
            play_stop_button_color = (0.694, 0.282, 0.282, 1.0)  # Red color for Stop button
        else:
            play_stop_button_label = "Play"
            play_stop_button_color = (0.282, 0.361, 0.306, 1.0)  # Green color for Play button

        # Set the button color
        imgui.push_style_color(imgui.COLOR_BUTTON, *play_stop_button_color)

        # Display the play/stop button for the current track
        if imgui.button(play_stop_button_label):
            if is_playing:
                pygame.mixer.Channel(0).stop()
            else:
                pygame.mixer.Channel(0).play(self.sounds[self.selected_track], loops=-1)

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
            if model.show_model:
                model.draw(
                    self.app.camera.projection.matrix,
                    self.app.camera.matrix,
                    self.light
                )

        self.grid.draw(self.app.camera.projection.matrix, self.app.camera)

        self.render_ui()

        for model_name in self.model_names_in_scene:
            model = self.find(model_name)
            if model.show_skeleton:
                bone_lines = get_bone_connections(model.get_root_bone())
                self.lines.update(bone_lines)
                self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix, model.get_model_matrix())

