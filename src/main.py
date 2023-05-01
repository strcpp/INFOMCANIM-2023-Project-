import moderngl_window as glw
import moderngl as gl
from render.shaders import Shaders
from render.mesh import Mesh
from scenes.basic_scene import BasicScene
import pathlib
import numpy as np
from loaders.gltf_loader import GLTFLoader
import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer

class App(glw.WindowConfig):
    title = "Computer anim. project"
    gl_version = (4, 5)
    window_size = (1600, 800)
    aspect_ratio = None
    resource_dir = (pathlib.Path(__file__).parent.parent / "resources").resolve()
    samples = 16

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = glw.scene.camera.OrbitCamera(aspect_ratio=self.wnd.aspect_ratio)
        # self.camera.mouse_sensitivity = 0.75
        self.camera.zoom_state(-2.5)

        self.mouse_pressed = False
        self.mouse_button = 0
        self.mpos = (0,0)
        self.mdelta = (0,0)
        self.loader = GLTFLoader(self)
        
        # initialize all assets
        Shaders.instance(self.ctx)
        Mesh.instance(self)

        imgui.create_context()

        self.imgui = ModernglWindowRenderer(self.wnd)

        self.scene = BasicScene(self)
        self.scene.load()

    def render(self, time, frametime):
        self.ctx.enable(gl.DEPTH_TEST)
        self.ctx.clear(color=(0.09, 0.12, 0.23))
        self.scene.update(frametime)
        self.scene.render()


    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        if action == keys.ACTION_PRESS and key == keys.ESCAPE:
            self.wnd.close()
        self.imgui.key_event(key, action, modifiers)

    def mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        if not imgui.get_io().want_capture_mouse:
            # pan camera, orbit camera class does not offer this for some reason..
            if self.mouse_button == 3:
                view_matrix = self.camera.matrix
                right = np.array(view_matrix.c1)
                up = np.array(view_matrix.c2)

                translation = dx * 0.01 * right + dy * 0.01 * up
                
                self.camera.target = [
                    self.camera.target[0] + translation[0],
                    self.camera.target[1] + translation[1],
                    self.camera.target[2] + translation[2]
                ]
            else:
                self.camera.rot_state(dx, dy)

        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        self.camera.zoom_state(y_offset)
        self.imgui.mouse_scroll_event(x_offset, y_offset)
    
    def resize(self, width: int, height: int):
        self.camera.projection.update(aspect_ratio=self.wnd.aspect_ratio)
        self.imgui.resize(width, height)

    def mouse_press_event(self, x, y, button):
        self.mouse_pressed = True
        self.mouse_button = button
        self.imgui.mouse_press_event(x, y, button) 

    def mouse_release_event(self, x, y, button):
        self.mouse_pressed = False
        self.mouse_button = None 
        self.imgui.mouse_release_event(x, y, button)

    def mouse_position_event(self, x,y,dx, dy):
        self.mpos = (x,y)
        self.mdelta = (dx, dy)
        self.imgui.mouse_position_event(x, y, dx, dy)

    def unicode_char_entered(self, char):
        self.imgui.unicode_char_entered(char)

if __name__ == '__main__':
    App.run()