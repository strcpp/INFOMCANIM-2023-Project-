
from abc import ABC, abstractmethod
from render.mesh import Mesh

class Scene():
    def __init__(self, app):
        self.app = app
        self.entities = []
    
    def add_entity(self, entity):
        self.entities.append(entity)

    @abstractmethod
    def load(self):
        pass
    
    @abstractmethod
    def unload(self):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def render(self):
        pass