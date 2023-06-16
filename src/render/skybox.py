import imageio as io
import os
from render.shaders import Shaders
import numpy as np
from pyrr import Matrix44, Matrix33

class Skybox:
    def __init__(self, app, skybox: str, ext: str = 'png'):
        self.app = app
        programs = Shaders.instance()
        self.skybox_prog = programs.get('skybox')

        faces = ['right', 'left', 'top', 'bottom', 'front', 'back']
        skybox_resources = os.path.join(os.path.dirname(__file__), f'../../resources/skyboxes/{skybox}/')
        textures = [io.imread(skybox_resources + f'{face}.{ext}') for face in faces]

        size = textures[0].shape
        self.texture_cube = self.app.ctx.texture_cube((size[0], size[1]), components=3, data=None)

        for i in range(6):
            self.texture_cube.write(face=i, data=textures[i].data)

        z = 0.9999
        vertices = [(-1, -1, z), (3, -1, z), (-1, 3, z)]
        vertex_data = np.array(vertices, dtype='f4')
        self.vbo = self.app.ctx.buffer(vertex_data) 

        self.skybox_prog['u_texture_skybox'] = 0
        self.texture_cube.use(location=0)

        self.vao = self.app.ctx.simple_vertex_array(self.skybox_prog, self.vbo, 'position')

    def draw(self, proj_matrix: np.ndarray, view_matrix: np.ndarray):
        view = Matrix44.from_matrix33(Matrix33.from_matrix44(view_matrix))
        view.r4[2] = -4.5
        view.r4[0] = -1.7524061e-16
        print(proj_matrix * view_matrix)
        print(proj_matrix * view)
        invpm = np.linalg.inv(proj_matrix * view_matrix)
        invpm2 = np.linalg.inv(proj_matrix * view)
        invpm2[1][3] = -5.7133058e-09
        print(invpm)
        print(invpm2)
        # print(self.app.camera.yaw)
        # print(view_matrix)
        # print(view)
        # print(proj_matrix)
        # print(proj_matrix * view)
        # print(proj_matrix * view_matrix)
        # print(proj_matrix @ view_matrix)
        print("\n")
        self.skybox_prog['m_invProjView'].write(invpm)
        self.vao.render()