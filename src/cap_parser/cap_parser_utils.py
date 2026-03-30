from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Structure

T = TypeVar("T", bound=Structure)


class Utils:

    @staticmethod
    def load_structure_array(cap_file: CapFile, raw: bytes, start_offset: int, count: int, structure_type: type[T]) -> tuple[int, list[T]]:
        structures = []
        for _ in range(count):
            structure = structure_type.load(cap_file, raw, start_offset)
            start_offset += structure.size
            structures.append(structure)

        return start_offset, structures

    @staticmethod
    def structure_list_to_bytes(structure_list: list[Structure]) -> bytearray:
        raw = bytearray()
        for structure in structure_list:
            raw.extend(structure.to_bytes())
        return raw

    @staticmethod
    def load_u2_array(raw: bytes, start_offset: int, count: int) -> tuple[int, list[int]]:
        result_list = []
        for _ in range(count):
            entry = int.from_bytes(raw[start_offset: start_offset + 2])
            result_list.append(entry)
            start_offset += 2
        return start_offset, result_list

    @staticmethod
    def size_of_structure_array(structure_array: list[Structure]) -> int:
        return sum([structure.size for structure in structure_array])

    @staticmethod
    def is_flag_set(flags: int, flag_masks: dict[str, int], flag_name: str) -> bool:
        assert flag_name in flag_masks.keys()
        return flags & flag_masks[flag_name] == flag_masks[flag_name]