from render.model import Model
from render.lines import Lines
from scenes.scene import Scene
from pyrr import quaternion as q, Matrix44, Vector3, Vector4
from light import Light
import imgui
import numpy as np
import time

def get_bone_connections(bone, parent_position=None):
    bone_connections = []

    if bone.rest_transform is not None:
        bone_position = bone.current_transform[-1, :3]

        if parent_position is not None:
            bone_connections.append((parent_position, bone_position))

        if bone.children:
            for child in bone.children:
                bone_connections.extend(get_bone_connections(child, bone_position))

    return bone_connections

class BasicScene(Scene):

    def load(self):
        self.add_entity(Model(self.app, 'Vampire'))
        self.bones = self.entities[0].get_bones()

        bone_lines = get_bone_connections(self.bones)
        self.lines = Lines(self.app, lineWidth=1, lines=bone_lines) 

        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'), 
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

        self.show_skeleton = True 
        self.show_model = True

        self.timestamp = 0.0

    def unload(self):
        pass

    def update(self, dt):
        self.timestamp += dt
        self.bones.update(self.timestamp)
        bone_lines = get_bone_connections(self.bones)
        self.lines.update(bone_lines)

        # speed = 0.5
        # angle = dt * speed
        # rotation =q.cross(self.entities[0].rotation, q.create_from_y_rotation(angle)) 
        # self.entities[0].rotation = rotation
        # self.lines.rotation = rotation

    def render_ui(self):
        imgui.new_frame()

        # Add an ImGui window
        imgui.begin("Settings")
        imgui.set_next_window_size(400,300)

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")
        
         # Add a slider for line thickness
        thickness_min = 1
        thickness_max = 15
        thickness_value = self.lines.lineWidth
        _, self.lines.lineWidth  = imgui.slider_float("Line Thickness", thickness_value, thickness_min, thickness_max)
        
        _, self.show_skeleton = imgui.checkbox("Skeleton", self.show_skeleton)
        _, self.show_model = imgui.checkbox("Model", self.show_model)


        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def render(self):
        if(self.show_model):
            for entity in self.entities:
                entity.draw(
                    self.app.camera.projection.matrix,
                    self.app.camera.matrix,
                    self.light
                )

        self.render_ui()
        if self.show_skeleton:
            self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)