from abc import abstractmethod
from render.model import Model


class Scene:
    def __init__(self, app) -> None:
        self.app = app
        self.entities = []

    def add_entity(self, entity: Model) -> None:
        self.entities.append(entity)

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
