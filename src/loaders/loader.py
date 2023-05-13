from abc import ABC, abstractmethod


class Loader:
    def __init__(self, app) -> None:
        self.app = app

    @abstractmethod
    def from_file(self, file_path: str) -> None:
        pass
