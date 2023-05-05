import os

"""
This class reads all models/textures from the resources/models folder, 
and creates corresponding GPU assets for them (vao, textures)
these can then be loaded into a "model" instance using their folder names
"""
class Mesh():
    _instance = None

    @classmethod
    def instance(cls, ctx=None):
        if cls._instance is None and ctx is not None:
            cls._instance = cls(ctx)
        return cls._instance

    def __init__(self, app):
        if Mesh._instance is not None:
            raise RuntimeError("Mesh is a singleton and should not be instantiated more than once")

        self.app = app
        self.data = {}

        models_path = os.path.join(os.path.dirname(__file__), '../../resources/models')

        for root, dirs, files in os.walk(models_path):
            for filename in files:
                if os.path.splitext(filename)[1] == '.gltf' or os.path.splitext(filename)[1] == '.glb':
                    name = os.path.basename(root)
                    model_file_path = os.path.normpath(os.path.join(root, filename))
                    self.data[name] = self.app.loader.from_file(model_file_path)
