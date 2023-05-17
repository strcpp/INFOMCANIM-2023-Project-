from abc import abstractmethod
from render.model import Model


class Entity:
    def __init__(self, name: str, model: Model):
        self.name = name
        self.model = model


class Scene:
    def __init__(self, app) -> None:
        self.app = app
        self.entities = []

    def add_entity(self, name, model: Model) -> None:
        self.entities.append(Entity(name, model))

    def find(self, name) -> Model:
        for entity in self.entities:
            if entity.name == name:
                return entity.model
        return None

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def unload(self) -> None:
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def render(self) -> None:
        pass
