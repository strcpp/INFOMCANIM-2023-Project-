from render.mesh import Mesh
from pyrr import quaternion as q, Quaternion, Vector3, Matrix44
import numpy as np

class Model():
    def __init__(self, app, mesh_name):
        meshes = Mesh.instance()
        self.app = app
        self.commands = meshes.commands[mesh_name]
        
        self.use_texture = False   
        if any(command[1] is not None for command in self.commands):
            self.textures = [command[1] for command in self.commands]
            self.use_texture = True
        
        self.transformation_matrix = None
        
        if any(command[3] is not None  for command in self.commands):
            self.transformation_matrix = [command[3] for command in self.commands]

        self.translation = Vector3()
        self.rotation = Quaternion()
        self.scale = Vector3([1.0, 1.0, 1.0])

    def get_model_matrix(self):
        trans = Matrix44.from_translation(self.translation)
        rot = Matrix44.from_quaternion(self.rotation)
        scale = Matrix44.from_scale(self.scale)
        model = trans * rot * scale

        if self.transformation_matrix is not None:
            model = model * self.transformation_matrix

        return np.array(model, dtype='f4')

    def draw(self, proj_matrix, view_matrix, light):
        for i, command in enumerate(self.commands):
            prog, texture, vao = command[2], command[1], command[0]
            
            prog['light.Ia'].write(light.Ia)
            prog['light.Id'].write(light.Id)
            prog['light.Is'].write(light.Is)
            prog['light.position'].write(light.position)
            prog['camPos'].write(np.array(self.app.camera.position, dtype='f4'))

            prog['model'].write(self.get_model_matrix())
            prog['view'].write(view_matrix)
            prog['projection'].write(proj_matrix)
            prog['useTexture'].value = self.use_texture

            if self.use_texture and texture is not None:
                texture.use()
            
            vao.render()