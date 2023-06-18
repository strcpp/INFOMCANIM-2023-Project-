from abc import abstractmethod


class Loader:
    """
    Abstract base class for loaders that can load data from a file.
    """
    def __init__(self, app) -> None:
        """
        Constructor.
        :param app: Glw app.
        """
        self.app = app

    @abstractmethod
    def from_file(self, file_path: str) -> None:
        """
        Abstract method for loading data from a file.
        :param file_path: File path.
        """
        pass
