from __future__ import annotations
from abc import abstractmethod, ABC


class Structure(ABC):

    @property
    @abstractmethod
    def size(self) -> int:
        pass

    @staticmethod
    @abstractmethod
    def load(raw: bytes, start_offset: int = 0) -> Structure:
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


class Component(Structure):


    @staticmethod
    @abstractmethod
    def load_from_file(filename: str) -> Component:
        pass

    @abstractmethod
    def export_to_directory(self, directory_name: str) -> None:
        pass

    @abstractmethod
    def pretty_print(self) -> None:
        pass

