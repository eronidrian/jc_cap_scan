from __future__ import annotations
from abc import abstractmethod, ABC

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile


class Structure(ABC):

    def __init__(self, cap_file: CapFile):
        self.cap_file = cap_file

    @property
    @abstractmethod
    def size(self) -> int:
        pass

    @staticmethod
    @abstractmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> Structure:
        pass

    @abstractmethod
    def to_bytes(self) -> bytearray:
        pass

    @abstractmethod
    def __str__(self):
        pass


class Component(Structure):

    def __init__(self, cap_file: CapFile):
        super().__init__(cap_file)

    @property
    @abstractmethod
    def tag(self) -> int:
        pass

    @property
    @abstractmethod
    def filename(self) -> str:
        pass

    @classmethod
    def load_from_file(cls, cap_file: CapFile, filename: str) -> Component:
        with open(filename, "rb") as f:
            raw = f.read()
        return cls.load(cap_file, raw, 0)

    @staticmethod
    @abstractmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> Component:
        pass

    def export_to_file(self, file_name: str) -> None:
        with open(file_name, "wb") as f:
            f.write(self.to_bytes())

    @abstractmethod
    def pretty_print(self) -> None:
        pass

    @abstractmethod
    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.append(self.tag)
        raw.extend(int.to_bytes(self.size, 2))
        return raw