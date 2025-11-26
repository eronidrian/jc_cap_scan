from __future__ import annotations

import os.path

from cap_parser.component import Component, Structure
from cap_parser.constants import COMPONENT_Import


class PackageInfo(Structure):

    def __init__(self, minor_version: int, major_version: int, aid: bytes):
        assert minor_version < 255
        assert major_version < 255
        self.minor_version = minor_version
        self.major_version = major_version
        self.aid = aid

    @property
    def aid_hex(self):
        return self.aid.hex().lower()

    @property
    def size(self):
        return 3 + len(self.aid)  # minor, major version, aid len and aid itself

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> PackageInfo:
        minor_version = raw[start_offset + 0]
        major_version = raw[start_offset + 1]
        aid_length = raw[start_offset + 2]
        aid = raw[start_offset + 3: start_offset + 3 + aid_length]

        return PackageInfo(minor_version, major_version, aid)

    def __str__(self):
        return (f"AID: {self.aid_hex}\n"
                f"Major version: {self.major_version}\n"
                f"Minor version: {self.minor_version}\n")

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.minor_version)
        raw.append(self.major_version)
        raw.append(len(self.aid))
        raw.extend(self.aid)
        return bytes(raw)


class ImportComponent(Component):
    filename = "Import.cap"
    tag = COMPONENT_Import

    def __init__(self, packages: list[PackageInfo]):
        self.count = len(packages)
        self.packages = packages

        assert self.count <= 128

    @property
    def size(self) -> int:
        return 1 + sum([package_info.size for package_info in self.packages])

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> ImportComponent:
        assert raw[start_offset + 0] == ImportComponent.tag

        count = raw[start_offset + 3]
        packages = []
        offset = 0
        for package_num in range(count):
            package_info = PackageInfo.load(raw[start_offset + 4:], offset)
            offset += package_info.size
            packages.append(package_info)

        return ImportComponent(packages)

    @staticmethod
    def load_from_file(filename: str) -> ImportComponent:
        with open(filename, "rb") as f:
            raw = f.read()

        return ImportComponent.load(raw)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(ImportComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        raw.append(len(self.packages))
        for package_info in self.packages:
            raw.extend(package_info.to_bytes())
        return bytes(raw)

    def export_to_directory(self, directory_name: str) -> None:
        with open(os.path.join(directory_name, ImportComponent.filename), "wb") as f:
            f.write(self.to_bytes())

    def pretty_print(self) -> None:
        print("Import component\n")
        for package_info in self.packages:
            print(package_info)


# import_component = ImportComponent.load_from_file("../template_method/applets/javacard/Import.cap")
# new_package_info = PackageInfo(12, 3, bytes.fromhex("a000ef"))
# import_component.packages.append(new_package_info)
# import_component.export_to_directory("..")
# import_component = ImportComponent.load_from_file("../Import.cap")
# import_component.pretty_print()
