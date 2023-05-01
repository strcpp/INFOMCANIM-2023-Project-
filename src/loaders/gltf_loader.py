from render.shaders import Shaders
from loaders.loader import Loader
from pygltflib import *
import numpy as np
import struct
import os

# helper class for loading gltf files
class GLTFLoader(Loader):

    def get_positions_data(self, gltf, primitive):
        positions_accessor = gltf.accessors[primitive.attributes.POSITION]
        positions_buffer_view = gltf.bufferViews[positions_accessor.bufferView]
        positions_buffer = gltf.buffers[positions_buffer_view.buffer]
        positions_data = gltf.get_data_from_buffer_uri(positions_buffer.uri)

        vertices = []
        for i in range(positions_accessor.count):
            index = positions_buffer_view.byteOffset + positions_accessor.byteOffset + i * 12
            d = positions_data[index:index+12]
            v = struct.unpack("<fff", d)
            vertices.append(v)

        return np.array(vertices, dtype='f4').reshape(-1, 3)

    def get_normals_data(self, gltf, primitive):
        normals_accessor = gltf.accessors[primitive.attributes.NORMAL]
        normals_buffer_view = gltf.bufferViews[normals_accessor.bufferView]
        normals_buffer = gltf.buffers[normals_buffer_view.buffer]
        normals_data = gltf.get_data_from_buffer_uri(normals_buffer.uri)

        normals = []
        for i in range(normals_accessor.count):
            index = normals_buffer_view.byteOffset + normals_accessor.byteOffset + i * 12
            d = normals_data[index:index+12]
            v = struct.unpack("<fff", d)
            normals.append(v)

        return np.array(normals, dtype='f4').reshape(-1, 3)

    def get_texcoords_data(self, gltf, primitive):
        if primitive.attributes.TEXCOORD_0:
            texcoords_accessor = gltf.accessors[primitive.attributes.TEXCOORD_0]
            texcoords_buffer_view = gltf.bufferViews[texcoords_accessor.bufferView]
            texcoords_buffer = gltf.buffers[texcoords_buffer_view.buffer]
            texcoords_data = gltf.get_data_from_buffer_uri(texcoords_buffer.uri)

            texcoords = []
            for i in range(texcoords_accessor.count):
                index = texcoords_buffer_view.byteOffset + texcoords_accessor.byteOffset + i * 8
                d = texcoords_data[index:index+8]
                v = struct.unpack("<ff", d)
                texcoords.append(v)

            texcoords = [(u, 1 - v) for u, v in texcoords]
        else:
            texcoords = [(0.0, 0.0) for _ in range(len(vertices))]
        
        return np.array(texcoords, dtype='f4').reshape(-1, 2)

    def get_indices_data(self, gltf, primitive):
        indices_accessor = gltf.accessors[primitive.indices]
        indices_buffer_view = gltf.bufferViews[indices_accessor.bufferView]
        indices_buffer = gltf.buffers[indices_buffer_view.buffer]
        indices_data = gltf.get_data_from_buffer_uri(indices_buffer.uri)

        indices = []
        for i in range(indices_accessor.count):
            if indices_accessor.componentType == UNSIGNED_INT:
                offset = 4
                stype = "<I"
            elif indices_accessor.componentType == UNSIGNED_SHORT:
                offset = 2
                stype = "<H"
            elif indices_accessor.componentType == UNSIGNED_BYTE:
                offset = 1
                stype = "<B"

            index = indices_buffer_view.byteOffset + indices_accessor.byteOffset + i * offset
            idx = struct.unpack(stype, indices_data[index:index+offset])[0]
            indices.append(idx)

        return np.array(indices, dtype='i4')

    def from_file(self, file_path):
        gltf = GLTF2().load(file_path)
        
        programs = Shaders.instance()
        prog = programs.get('base')

        mesh = gltf.meshes[gltf.scenes[gltf.scene].nodes[0]]
        commands = []

        for primitive in mesh.primitives:

            vertices = self.get_positions_data(gltf, primitive)
            normals = self.get_normals_data(gltf, primitive)
            texcoords = self.get_texcoords_data(gltf, primitive)
            indices = self.get_indices_data(gltf, primitive)
            
            vertex_data = np.hstack((vertices, normals, texcoords))

            vbo = self.app.ctx.buffer(vertex_data.astype('f4'))
            ibo = self.app.ctx.buffer(indices)

            texture = None
            if(primitive.attributes.TEXCOORD_0):
                # Load the texture
                material = gltf.materials[primitive.material]
                texture_index = material.pbrMetallicRoughness.baseColorTexture.index
                texture = gltf.textures[texture_index]
                image = gltf.images[texture.source]
                texture_path = os.path.join(os.path.dirname(file_path), image.uri)
                texture = self.app.load_texture_2d(texture_path)

            # Create VAO
            vao_content = [
                (vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_texcoord_0')
            ]
            
            mesh_node_index = gltf.scenes[gltf.scene].nodes[0]
            mesh_node = gltf.nodes[mesh_node_index]
            transformation_matrix = None

            if mesh_node.matrix is not None:
                transformation_matrix = np.array(mesh_node.matrix, dtype='f4').reshape(4, 4)

            commands.append((self.app.ctx.vertex_array(prog, vao_content,ibo), texture, prog, transformation_matrix))

        return commands