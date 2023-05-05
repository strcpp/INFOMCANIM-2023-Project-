import numpy as np
from pyrr import quaternion as q, Quaternion, Vector3, Matrix44
from render.shaders import Shaders
import moderngl

class Lines():
    def __init__(self, app, lineWidth = 1, color=[0,0,1,1], lines = []):
        self.app = app
        self.lineWidth = lineWidth
        self.color = color
        programs = Shaders.instance()
        self.line_prog = programs.get('lines')
        self.lines = lines

        vertex, index = self.build_lines(lines)

        vbo = self.app.ctx.buffer(vertex)
        ibo = self.app.ctx.buffer(index)
        self.vao = self.app.ctx.simple_vertex_array(self.line_prog, vbo, "position",
                                                index_buffer=ibo)

        self.translation = Vector3()
        self.rotation = Quaternion()
        self.scale = Vector3([1.0, 1.0, 1.0])


    def build_lines(self, lines):
        vertices = []
        indices = []
        index_counter = 0

        for line in lines:
            start, end = line
            vertices.extend(start)
            vertices.extend(end)

            indices.append(index_counter)
            indices.append(index_counter + 1)

            index_counter += 2

        vertex_data = np.array(vertices, dtype=np.float32)
        index_data = np.array(indices, dtype=np.uint32)

        return vertex_data, index_data

    def get_model_matrix(self):
        trans = Matrix44.from_translation(self.translation)
        rot = Matrix44.from_quaternion(self.rotation)
        scale = Matrix44.from_scale(self.scale)
        model = trans * rot * scale

        return np.array(model, dtype='f4')

    def draw(self, proj_matrix, view_matrix):
        self.line_prog["img_width"].value = self.app.window_size[0]
        self.line_prog["img_height"].value =  self.app.window_size[1]
        self.line_prog["line_thickness"].value = self.lineWidth

        self.line_prog['model'].write(self.get_model_matrix())
        self.line_prog['view'].write(view_matrix)
        self.line_prog['projection'].write(proj_matrix)

        self.vao.render(moderngl.LINES)