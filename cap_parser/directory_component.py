from __future__ import annotations

import os.path
import textwrap

from cap_parser.component import Component, Structure
from cap_parser.constants import COMPONENT_Directory, component_names


class StaticFieldSizeInfo(Structure):

    def __init__(self, image_size: int, array_init_count: int, array_init_size: int):
        self.image_size = image_size
        self.array_init_count = array_init_count
        self.array_init_size = array_init_size

    @property
    def size(self) -> int:
        return 6

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> StaticFieldSizeInfo:
        raw = raw[start_offset:]
        image_size = int.from_bytes(raw[0:2])
        array_init_count = int.from_bytes(raw[2:4])
        array_init_size = int.from_bytes(raw[4:6])

        return StaticFieldSizeInfo(image_size, array_init_count, array_init_size)

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

    def __init__(self, component_tag: int, component_size: int, aid: bytes):
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
    def load(raw: bytes, start_offset: int = 0) -> CustomComponentInfo:
        raw = raw[start_offset:]

        component_tag = raw[0]
        component_size = int.from_bytes(raw[1:3])
        aid_length = raw[3]
        aid = raw[4 : 4 + aid_length]

        return CustomComponentInfo(component_tag, component_size, aid)

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

    tag = COMPONENT_Directory
    filename = "Directory.cap"

    def __init__(self, component_sizes: list[int], static_field_size: StaticFieldSizeInfo, import_count: int, applet_count: int, custom_components: list[CustomComponentInfo]):
        self.component_sizes = component_sizes
        self.static_field_size = static_field_size
        self.import_count = import_count
        self.applet_count = applet_count
        self.custom_components = custom_components

    @property
    def custom_count(self) -> int:
        return len(self.custom_components)

    @property
    def component_sizes_pretty(self) -> str:
        result_string = ""
        for i, component_name in enumerate(component_names):
            result_string += f"{component_name}: {self.component_sizes[i]}\n"
        return result_string


    @staticmethod
    def load_from_file(filename: str) -> DirectoryComponent:
        with open(filename, "rb") as f:
            raw = f.read()

        return DirectoryComponent.load(raw, 0)


    def export_to_directory(self, directory_name: str) -> None:
        with open(os.path.join(directory_name, DirectoryComponent.filename), "wb") as f:
            f.write(self.to_bytes())

    def pretty_print(self) -> None:
        print("Directory component")
        print()
        print("Component sizes:")
        print(textwrap.indent(self.component_sizes_pretty, "\t"))
        print("Static field size:")
        print(textwrap.indent(str(self.static_field_size), "\t"))
        print(f"Import count: {self.import_count}")
        print(f"Applet count: {self.applet_count}")
        print("Custom components:")
        for custom_component in self.custom_components:
            print(textwrap.indent(str(custom_component), "\t"))


    @property
    def size(self) -> int:
        return self.static_field_size.size + 3 + sum([custom_component.size for custom_component in self.custom_components])

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> DirectoryComponent:
        raw = raw[start_offset:]
        assert raw[0] == DirectoryComponent.tag

        component_sizes_bytes = raw[3 : 25] # component sizes contains only 11 entries, contrary to the specification
        component_sizes = []
        for i in range(0, 22, 2):
            component_sizes.append(int.from_bytes(component_sizes_bytes[i : i + 2]))
        static_field_size = StaticFieldSizeInfo.load(raw, 25)
        import_count = raw[25 + static_field_size.size]
        applet_count = raw[26 + static_field_size.size]

        custom_count = raw[27 + static_field_size.size]
        custom_components = []
        offset = 0
        for custom_count_num in range(custom_count):
            custom_component_info = CustomComponentInfo.load(raw[28 + static_field_size.size:], offset)
            offset += custom_component_info.size
            custom_components.append(custom_component_info)

        return DirectoryComponent(component_sizes, static_field_size, import_count, applet_count, custom_components)


    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(DirectoryComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        for component_size in self.component_sizes:
            raw.extend(int.to_bytes(component_size, 2))
        raw.extend(self.static_field_size.to_bytes())
        raw.append(self.import_count)
        raw.append(self.applet_count)
        raw.append(self.custom_count)
        for custom_component_info in self.custom_components:
            raw.extend(custom_component_info.to_bytes())
        return bytes(raw)


directory_component = DirectoryComponent.load_from_file("../template_method/applets/javacard/Directory.cap")
directory_component.export_to_directory("..")
directory_component = DirectoryComponent.load_from_file("../Directory.cap")
directory_component.pretty_print()