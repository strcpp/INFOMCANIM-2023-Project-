from render.model import Model
from scenes.scene import Scene
from pyrr import quaternion as q, Matrix44, Vector3
from light import Light
import imgui

class BasicScene(Scene):
    def load(self):
        self.add_entity(Model(self.app, 'Vampire'))

        self.light = Light(
            position=Vector3([5., 5., 5.], dtype='f4'), 
            color=Vector3([1.0, 1.0, 1.0], dtype='f4')
        )

    def unload(self):
        pass

    def update(self, dt):
        speed = 0.5
        angle = dt * speed
        self.entities[0].rotation = q.cross(self.entities[0].rotation, q.create_from_y_rotation(angle))

    def render_ui(self):
        imgui.new_frame()

        # Add an ImGui window
        imgui.begin("Settings")
        imgui.set_next_window_size(400,300)

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def handle_select_animation(self, selected_animation):
        pass

    def render(self):
        for entity in self.entities:
            entity.draw(
                self.app.camera.projection.matrix,
                self.app.camera.matrix,
                self.light
            )

        self.render_ui()