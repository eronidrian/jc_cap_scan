from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from cap_parser.constants import ComponentTags

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile

from cap_parser.component import Component, Structure


class ArrayInitInfo(Structure):

    def __init__(self, cap_file: CapFile, _type: int, values: list[int]):
        super().__init__(cap_file)
        self._type = _type
        self.values = values

    @property
    def count(self) -> int:
        return len(self.values)

    @property
    def size(self) -> int:
        return 3 + self.count

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ArrayInitInfo:
        raw = raw[start_offset:]
        _type = raw[0]
        count = int.from_bytes(raw[1:2])
        values = [raw[2 + offset] for offset in range(count)]
        return ArrayInitInfo(cap_file, _type, values)

    def to_bytes(self) -> bytes:
        pass

    def __str__(self):
        return (f"Type: {self._type}\n"
                f"Values: {self.values}\n")

class StaticFieldComponent(Component):
    tag = ComponentTags.CONSTANT_StaticField
    filename = "StaticField.cap"

    def __init__(self, cap_file: CapFile, reference_count: int, array_init: list[ArrayInitInfo],
                 default_value_count: int, non_default_values: list[int]):
        super().__init__(cap_file)
        self.reference_count = reference_count
        self.array_init = array_init
        self.default_value_count = default_value_count
        self.non_default_values = non_default_values

    @property
    def image_size(self) -> int:
        return self.reference_count * 2 + self.default_value_count + self.non_default_value_count

    @property
    def array_init_count(self) -> int:
        return len(self.array_init)

    @property
    def non_default_value_count(self) -> int:
        return len(self.non_default_values)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticFieldComponent:
        raw = raw[start_offset:]
        assert raw[0] == StaticFieldComponent.tag

        reference_count = int.from_bytes(raw[5:7])
        array_init_count = int.from_bytes(raw[7:9])
        array_init = []
        offset = 9
        for _ in range(array_init_count):
            array_init_info = ArrayInitInfo.load(cap_file, raw, offset)
            offset += array_init_info.size
            array_init.append(array_init_info)

        default_value_count = int.from_bytes(raw[offset : offset + 2])
        offset += 2
        non_default_value_count = int.from_bytes(raw[offset : offset + 2])
        offset +=2
        non_default_values = []
        for _ in range(non_default_value_count):
            non_default_values.append(raw[offset])
            offset +=1
        return StaticFieldComponent(cap_file, reference_count, array_init, default_value_count, non_default_values)

    def pretty_print(self) -> None:
        print("Static field component")
        print()
        print(f"Image size: {self.image_size}")
        print(f"Reference count: {self.reference_count}")
        print("Array init:")
        for array_init_info in self.array_init:
            print(textwrap.indent(str(array_init_info), "\t"))
        print(f"Default value count: {self.default_value_count}")
        print(f"Non default values: {self.non_default_values}")

    @property
    def size(self) -> int:
        return 6 + sum([array_init_info.size for array_init_info in self.array_init]) + 4 + self.non_default_value_count

    def to_bytes(self) -> bytes:
        pass
