from render.shaders import Shaders
from loaders.loader import Loader
from pygltflib import *
import numpy as np
import struct
import os
from loaders.gltf_loader_helpers import *

# helper class for loading gltf files
class GLTFLoader(Loader):

    def get_accessor_data(self, gltf, accessor, dtype):
        buffer_view = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[buffer_view.buffer]
        data = gltf.get_data_from_buffer_uri(buffer.uri)

        byte_offset = buffer_view.byteOffset + accessor.byteOffset
        dtype_format = accessor_type_fmt(accessor)
        component_size = struct.calcsize(dtype_format)

        values = []

        for i in range(accessor.count):
            start = byte_offset + i * component_size
            end = start + component_size
            chunk = data[start:end]
            value = struct.unpack(dtype_format, chunk)

            values.append(value)

        return np.array(values, dtype=dtype).reshape(-1, accessor_type_count(accessor))


    def from_file(self, file_path):
        gltf = GLTF2().load(file_path)
        
        programs = Shaders.instance()
        prog = programs.get('base')
        mesh = gltf.meshes[gltf.scenes[gltf.scene].nodes[0]]
        commands = []

        for primitive in mesh.primitives:

            positions_accessor = gltf.accessors[primitive.attributes.POSITION]
            positions = self.get_accessor_data(gltf, positions_accessor, 'f4')

            normals_accessor = gltf.accessors[primitive.attributes.NORMAL]
            normals = self.get_accessor_data(gltf, normals_accessor, 'f4')
            
            texture = None
            if primitive.attributes.TEXCOORD_0:
                texcoords_accessor = gltf.accessors[primitive.attributes.TEXCOORD_0]
                texcoords = self.get_accessor_data(gltf, texcoords_accessor, 'f4')
                texcoords = [(u, 1 - v) for u, v in texcoords]

                # Load the texture
                material = gltf.materials[primitive.material]
                texture_index = material.pbrMetallicRoughness.baseColorTexture.index
                texture = gltf.textures[texture_index]
                image = gltf.images[texture.source]
                texture_path = os.path.join(os.path.dirname(file_path), image.uri)
                texture = self.app.load_texture_2d(texture_path)
            else:
                texcoords = [(0.0, 0.0) for _ in range(len(positions))]

            indices_accessor = gltf.accessors[primitive.indices]
            indices = self.get_accessor_data(gltf, indices_accessor, 'i4')
            
            vertex_data = np.hstack((positions, normals, texcoords))

            vbo = self.app.ctx.buffer(vertex_data.astype('f4'))
            ibo = self.app.ctx.buffer(indices)

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