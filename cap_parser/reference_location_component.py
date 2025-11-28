from __future__ import annotations

import textwrap
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from api_specification.api_specification import JCMethodType

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags, CpInfoTags, API_SPECIFICATION

class ReferenceLocationComponent(Component):

    tag = ComponentTags.CONSTANT_ReferenceLocation
    filename = "RefLocation.cap"

    def __init__(self, cap_file: CapFile, offsets_to_byte_indices: list[int], offsets_to_byte2_indices: list[int]):
        super().__init__(cap_file)
        self.offsets_to_byte_indices = offsets_to_byte_indices
        self.offsets_to_byte2_indices = offsets_to_byte2_indices

    @property
    def byte_index_count(self) -> int:
        return len(self.offsets_to_byte_indices)

    @property
    def byte2_index_count(self) -> int:
        return len(self.offsets_to_byte2_indices)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ReferenceLocationComponent:
        raw = raw[start_offset:]
        assert raw[0] == ReferenceLocationComponent.tag

        byte_index_count = int.from_bytes(raw[3:5])
        offset =  5
        offsets_to_byte_indices = list(raw[5 : 5 + byte_index_count])
        offset += byte_index_count

        byte2_index_count = int.from_bytes(raw[offset : offset + 2])
        offset += 2
        offsets_to_byte2_indices = list(raw[offset : offset + byte2_index_count])
        return ReferenceLocationComponent(cap_file, offsets_to_byte_indices, offsets_to_byte2_indices)

    def pretty_print(self) -> None:
        print("Reference location component")
        print()
        print(f"Offsets to byte indices: {self.offsets_to_byte_indices}")
        print(f"Offsets to byte2 indices: {self.offsets_to_byte2_indices}")

    @property
    def size(self) -> int:
        return 2 + self.byte_index_count + 2 + self.byte2_index_count

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(int.to_bytes(self.byte_index_count, 2))
        raw.extend(bytes(self.offsets_to_byte_indices))
        raw.extend(int.to_bytes(self.byte2_index_count, 2))
        raw.extend(bytes(self.offsets_to_byte2_indices))
        return bytes(raw)
