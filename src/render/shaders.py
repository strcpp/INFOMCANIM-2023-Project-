
"""
This class loads/stores all shaders to be used by the program
"""
class Shaders():
    _instance = None

    @classmethod
    def instance(cls, ctx=None):
        if cls._instance is None and ctx is not None:
            cls._instance = cls(ctx)
        return cls._instance

    def __init__(self, ctx):
        if Shaders._instance is not None:
            raise RuntimeError("Shaders is a singleton and should not be instantiated more than once")
        self.shaders = {}
        self.ctx = ctx
        self.shaders['base'] = self.compile_shader('base')

    def compile_shader(self, name):
        with open(f'resources/shaders/{name}_vert.glsl') as file:
            vertex_shader = file.read()

        with open(f'resources/shaders/{name}_frag.glsl') as file:
            fragment_shader = file.read()

        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

    def get(self, name):
        return self.shaders[name]
        
    def destroy(self):
        [shader.release() for shader in self.shaders.values()]
