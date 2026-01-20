from __future__ import annotations

import textwrap

from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import component_names, ComponentTags


class StaticFieldSizeInfo(Structure):

    def __init__(self, cap_file: CapFile,  image_size: int, array_init_count: int, array_init_size: int):
        super().__init__(cap_file)
        self.image_size = image_size
        self.array_init_count = array_init_count
        self.array_init_size = array_init_size

    @property
    def size(self) -> int:
        return 6

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticFieldSizeInfo:
        raw = raw[start_offset:]
        image_size = int.from_bytes(raw[0:2])
        array_init_count = int.from_bytes(raw[2:4])
        array_init_size = int.from_bytes(raw[4:6])

        return StaticFieldSizeInfo(cap_file, image_size, array_init_count, array_init_size)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(int.to_bytes(self.image_size, 2))
        raw.extend(int.to_bytes(self.array_init_count, 2))
        raw.extend(int.to_bytes(self.array_init_size, 2))
        return bytes(raw)

    def __str__(self):
        return (f"Image size: {self.image_size}\n"
                f"Array init count: {self.array_init_count}\n"
                f"Array init size: {self.array_init_size}\n")


class CustomComponentInfo(Structure):

    def __init__(self, cap_file: CapFile, component_tag: int, component_size: int, aid: bytes):
        super().__init__(cap_file)
        self.component_tag = component_tag
        self.component_size = component_size
        self.aid = aid

    @property
    def aid_length(self) -> int:
        return len(self.aid)

    @property
    def aid_hex(self) -> str:
        return self.aid.hex().lower()

    @property
    def size(self) -> int:
        return 4 + self.aid_length

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> CustomComponentInfo:
        raw = raw[start_offset:]

        component_tag = raw[0]
        component_size = int.from_bytes(raw[1:3])
        aid_length = raw[3]
        aid = raw[4 : 4 + aid_length]

        return CustomComponentInfo(cap_file, component_tag, component_size, aid)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.component_tag)
        raw.extend(int.to_bytes(self.component_size, 2))
        raw.append(self.aid_length)
        raw.extend(self.aid)

        return bytes(bytearray)

    def __str__(self):
        return (f"Component tag: {self.component_tag}\n"
                f"Component size: {self.component_size}\n"
                f"AID: {self.aid_hex}")


class DirectoryComponent(Component):

    tag = ComponentTags.COMPONENT_Directory
    filename = "Directory.cap"

    def __init__(self, cap_file: CapFile, component_sizes: list[int], static_field_size: StaticFieldSizeInfo, custom_components: list[CustomComponentInfo]):
        super().__init__(cap_file)
        self.component_sizes = component_sizes
        self.static_field_size = static_field_size
        self.custom_components = custom_components

    @property
    def import_count(self) -> int:
        return self.cap_file.import_component.count

    @property
    def applet_count(self) -> int:
        return self.cap_file.applet_component.count


    @property
    def custom_count(self) -> int:
        return len(self.custom_components)

    @property
    def component_sizes_pretty(self) -> str:
        result_string = ""
        for i, component_name in enumerate(component_names):
            result_string += f"{component_name}: {self.component_sizes[i]}\n"
        return result_string

    def __str__(self):
        result_string = "Directory component\n\n"
        result_string += "Component sizes:\n"
        result_string += textwrap.indent(self.component_sizes_pretty, "\t")
        result_string += "Static field size:\n"
        result_string += textwrap.indent(str(self.static_field_size), "\t")
        result_string += f"Import count: {self.import_count}\n"
        result_string += f"Applet count: {self.applet_count}\n"
        result_string += "Custom components:\n"
        for custom_component in self.custom_components:
            result_string += textwrap.indent(str(custom_component), "\t") + "\n"
        return result_string

    def pretty_print(self) -> None:
        print(self.__str__())


    @property
    def size(self) -> int:
        return len(self.component_sizes) * 2 + self.static_field_size.size + 3 + Utils.size_of_structure_array(self.custom_components)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> DirectoryComponent:
        raw = raw[start_offset:]
        assert raw[0] == DirectoryComponent.tag

        offset, component_sizes = Utils.load_u2_array(raw, 3, 11) # component sizes contains only 11 entries, contrary to the specification

        static_field_size = StaticFieldSizeInfo.load(cap_file, raw, offset)
        offset += static_field_size.size
        offset += 2

        custom_count = raw[offset]
        offset += 1
        _, custom_components = Utils.load_structure_array(cap_file, raw, offset, custom_count, CustomComponentInfo)

        return DirectoryComponent(cap_file, component_sizes, static_field_size, custom_components)


    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        for component_size in self.component_sizes:
            raw.extend(int.to_bytes(component_size, 2))
        raw.extend(self.static_field_size.to_bytes())
        raw.append(self.import_count)
        raw.append(self.applet_count)
        raw.append(self.custom_count)
        for custom_component_info in self.custom_components:
            raw.extend(custom_component_info.to_bytes())
        return bytes(raw)
