import pygltflib as gltf
import struct
import numpy as np

def accessor_type_count(accessor):
    if accessor.type == "SCALAR":
        return 1
    elif accessor.type == "VEC2":
        return 2
    elif accessor.type == "VEC3":
        return 3
    elif accessor.type == "VEC4":
        return 4
    elif accessor.type == "MAT2":
        return 4
    elif accessor.type == "MAT3":
        return 9
    elif accessor.type == "MAT4":
        return 16
    else:
        raise ValueError(f"Unknown accessor type: {accessor.type}")

def accessor_component_type_fmt(accessor):
    if accessor.componentType == gltf.BYTE:
        return "b"
    elif accessor.componentType == gltf.UNSIGNED_BYTE:
        return "B"
    elif accessor.componentType == gltf.SHORT:
        return "h"
    elif accessor.componentType == gltf.UNSIGNED_SHORT:
        return "H"
    elif accessor.componentType == gltf.UNSIGNED_INT:
        return "I"
    elif accessor.componentType == gltf.FLOAT:
        return "f"
    else:
        raise ValueError(f"Unknown component type: {accessor.componentType}")

def accessor_type_fmt(accessor):
    fmt = accessor_component_type_fmt(accessor)
    if accessor.type == "SCALAR":
        return f'<{fmt}'
    elif accessor.type == "VEC2":
        return f'<{fmt * 2}'
    elif accessor.type == "VEC3":
        return f'<{fmt * 3}'
    elif accessor.type == "VEC4":
        return f'<{fmt * 4}'
    elif accessor.type == "MAT2":
        return f'<{fmt * 4}'
    elif accessor.type == "MAT3":
        return f'<{fmt * 9}'
    elif accessor.type == "MAT4":
        return f'<{fmt * 16}'
    else:
        raise ValueError(f"Unknown accessor type: {accessor.type}")

def get_image_data(gltf, bufferView):
    buffer_view = gltf.bufferViews[bufferView]
    buffer = gltf.buffers[buffer_view.buffer]
    data = gltf.get_data_from_buffer_uri(buffer.uri)

    start = buffer_view.byteOffset
    end = buffer_view.byteLength

    return data[start: start + end]


def get_accessor_data(gltf, accessor, dtype):
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