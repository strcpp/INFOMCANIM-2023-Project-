
from abc import ABC, abstractmethod

class Loader():
    def __init__(self, app):
        self.app = app
    
    @abstractmethod
    def from_file(self, file_path):
        pass