from render.lines import Lines
from scenes.scene import Scene
import imgui


class LinesScene(Scene):

    def load(self) -> None:
        lines = [
            ((-1.0, -1.0, 1.0), (1.0, -1.0, 1.0)),  # Front bottom edge
            ((1.0, -1.0, 1.0), (1.0, 1.0, 1.0)),  # Front right edge
            ((1.0, 1.0, 1.0), (-1.0, 1.0, 1.0)),  # Front top edge
            ((-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0)),  # Front left edge

            ((-1.0, -1.0, -1.0), (1.0, -1.0, -1.0)),  # Back bottom edge
            ((1.0, -1.0, -1.0), (1.0, 1.0, -1.0)),  # Back right edge
            ((1.0, 1.0, -1.0), (-1.0, 1.0, -1.0)),  # Back top edge
            ((-1.0, 1.0, -1.0), (-1.0, -1.0, -1.0)),  # Back left edge

            ((-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0)),  # Bottom left edge
            ((1.0, -1.0, 1.0), (1.0, -1.0, -1.0)),  # Bottom right edge
            ((1.0, 1.0, 1.0), (1.0, 1.0, -1.0)),  # Top right edge
            ((-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0))  # Top left edge
        ]

        self.lines = Lines(self.app, lineWidth=1, lines=lines)

    def unload(self) -> None:
        pass

    def update(self, dt: float) -> None:
        speed = 0.5
        angle = dt * speed

    def render_ui(self) -> None:
        imgui.new_frame()

        # Add an ImGui window
        imgui.begin("Settings")
        imgui.set_next_window_size(400, 300)

        imgui.text("Click and drag left/right mouse button to rotate camera.")
        imgui.text("Click and drag middle mouse button to pan camera.")

        # Add a slider for line thickness
        thickness_min = 1
        thickness_max = 15
        thickness_value = self.lines.lineWidth
        _, thickness_value = imgui.slider_float("Line Thickness", thickness_value, thickness_min, thickness_max)

        self.lines.lineWidth = thickness_value

        imgui.end()
        imgui.render()

        self.app.imgui.render(imgui.get_draw_data())

    def render(self) -> None:
        self.render_ui()
        self.lines.draw(self.app.camera.projection.matrix, self.app.camera.matrix)
