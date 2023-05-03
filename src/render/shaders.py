
"""
This class loads/stores all shaders to be used by the program
"""
class Shaders():
    _instance = None

    @classmethod
    def instance(cls, app=None):
        if cls._instance is None and app is not None:
            cls._instance = cls(app)
        return cls._instance

    def __init__(self, app):
        if Shaders._instance is not None:
            raise RuntimeError("Shaders is a singleton and should not be instantiated more than once")
        self.shaders = {}
        self.app = app
        self.shaders['base'] = self.app.load_program("shaders/base.glsl")
        self.shaders['lines'] = self.app.load_program("shaders/thicc_lines.glsl")


    def get(self, name):
        return self.shaders[name]
        
    def destroy(self):
        [shader.release() for shader in self.shaders.values()]
