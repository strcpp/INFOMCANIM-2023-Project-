import pygltflib as gltf

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