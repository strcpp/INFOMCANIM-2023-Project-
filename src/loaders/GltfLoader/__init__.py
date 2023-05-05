from render.shaders import Shaders
from loaders.loader import Loader
from pygltflib import *
import numpy as np
import struct
import os
from loaders.GltfLoader.gltf_loader_helpers import *
from loaders.GltfLoader.gltf_loader_animation import *
from PIL import Image
import io
import animation.animation as a

# helper class for loading gltf files
class GLTFLoader(Loader):

    def from_file(self, file_path):
        gltf = GLTF2().load(file_path)

        bones = None
        animation = None
        if(gltf.animations is not None):
            # let's just consider the first animation for now (which in our use case is good enough..)
            # adding multiple animations per file is trivial anyway
            animation_id = 0
            
            if(gltf.skins[animation_id] is not None):
                root_bone,bone_dict  = get_bones(gltf, gltf.skins[animation_id])
                duration = get_channels(gltf, animation_id, bone_dict)
                animation = a.Animation(gltf.animations[animation_id].name, duration, root_bone)
                animation.assert_channels_not_empty()


        programs = Shaders.instance()
        prog = programs.get('base')
        commands = []

        for mesh in gltf.meshes:
            for primitive in mesh.primitives:

                positions_accessor = gltf.accessors[primitive.attributes.POSITION]
                positions = get_accessor_data(gltf, positions_accessor, 'f4')

                normals_accessor = gltf.accessors[primitive.attributes.NORMAL]
                normals = get_accessor_data(gltf, normals_accessor, 'f4')
                
                texture = None
                if primitive.attributes.TEXCOORD_0 is not None:
                    
                    texcoords_accessor = gltf.accessors[primitive.attributes.TEXCOORD_0]
                    texcoords = get_accessor_data(gltf, texcoords_accessor, 'f4')

                    # Load the texture
                    material = gltf.materials[primitive.material]
                    if (material.pbrMetallicRoughness.baseColorTexture is not None):
                        # gltf.convert_images(ImageFormat.FILE)

                        texture_index = material.pbrMetallicRoughness.baseColorTexture.index
                        texture = gltf.textures[texture_index]
                        image = gltf.images[texture.source]
                        if(image.uri is None):
                            texture = get_image_data(gltf, image.bufferView)
                        else:
                            texture =  gltf.get_data_from_buffer_uri(image.uri)

                        img = Image.open( io.BytesIO(texture))
                        components = 4 if img.mode == 'RGBA' else 3
                        texture = self.app.ctx.texture(size=img.size, components=components,
                                                data=img.tobytes())
                else:
                    texcoords = [(0.0, 0.0) for _ in range(len(positions))]

                indices_accessor = gltf.accessors[primitive.indices]
                indices = get_accessor_data(gltf, indices_accessor, 'i4')
                
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

        return (commands, animation)