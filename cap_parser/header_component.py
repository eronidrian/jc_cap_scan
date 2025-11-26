from __future__ import annotations

import os.path

from cap_parser.component import Component, Structure
from cap_parser.constants import COMPONENT_Header
from cap_parser.import_component import PackageInfo


class HeaderComponent(Component):
    filename = "Header.cap"
    magic = bytes.fromhex("DECAFFED")
    tag = COMPONENT_Header

    def __init__(self, cap_format_minor_version: int, cap_format_major_version: int, flags: int, package: PackageInfo):
        self.cap_format_minor_version = cap_format_minor_version
        self.cap_format_major_version = cap_format_major_version
        self.flags = flags
        self.package = package

    @staticmethod
    def load_from_file(filename: str) -> HeaderComponent:
        with open(filename, "rb") as f:
            raw = f.read()
        return HeaderComponent.load(raw, 0)

    def export_to_directory(self, directory_name: str) -> None:
        with open(os.path.join(directory_name, HeaderComponent.filename), "wb") as f:
            f.write(self.to_bytes())

    def pretty_print(self) -> None:
        print("Header component")
        print()
        print(f"CAP format minor version: {self.cap_format_minor_version}")
        print(f"CAP format major version: {self.cap_format_major_version}")
        print(self.package)

    @property
    def size(self) -> int:
        return 10 + self.package.size

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> HeaderComponent:
        raw = raw[start_offset:]
        assert raw[0] == HeaderComponent.tag
        assert raw[3:7] == HeaderComponent.magic
        cap_format_minor_version = raw[7]
        cap_format_major_version = raw[8]
        flags = raw[9]
        package = PackageInfo.load(raw[10:], 0)
        return HeaderComponent(cap_format_minor_version, cap_format_major_version, flags, package)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(HeaderComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        raw.extend(HeaderComponent.magic)
        raw.append(self.cap_format_minor_version)
        raw.append(self.cap_format_major_version)
        raw.append(self.flags)
        raw.extend(self.package.to_bytes())

        return bytes(raw)


header_component = HeaderComponent.load_from_file("../template_method/applets/javacard/Header.cap")
header_component.export_to_directory("..")
header_component = HeaderComponent.load_from_file("../Header.cap")
header_component.pretty_print()
