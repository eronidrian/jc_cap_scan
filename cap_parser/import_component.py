from __future__ import annotations

import textwrap

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags, API_SPECIFICATION


class PackageInfo(Structure):

    def __init__(self, cap_file: CapFile, minor_version: int, major_version: int, aid: bytes):
        assert minor_version < 255
        assert major_version < 255
        super().__init__(cap_file)
        self.minor_version = minor_version
        self.major_version = major_version
        self.aid = aid

    @property
    def aid_length(self) -> int:
        return len(self.aid)

    @property
    def aid_hex(self):
        return self.aid.hex().lower()

    @property
    def size(self):
        return 3 + self.aid_length  # minor, major version, aid len and aid itself

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> PackageInfo:
        minor_version = raw[start_offset + 0]
        major_version = raw[start_offset + 1]
        aid_length = raw[start_offset + 2]
        aid = raw[start_offset + 3: start_offset + 3 + aid_length]

        return PackageInfo(cap_file, minor_version, major_version, aid)

    def __str__(self):
        return (f"AID: {self.aid_hex} ({API_SPECIFICATION.get_package_by_aid(self.aid_hex).name})\n"
                f"Major version: {self.major_version}\n"
                f"Minor version: {self.minor_version}\n")

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.minor_version)
        raw.append(self.major_version)
        raw.append(self.aid_length)
        raw.extend(self.aid)
        return bytes(raw)


class ImportComponent(Component):
    tag = ComponentTags.COMPONENT_Import
    filename = "Import.cap"

    def __init__(self, cap_file: CapFile, packages: list[PackageInfo]):
        super().__init__(cap_file)
        self.packages = packages

    @property
    def count(self) -> int:
        return len(self.packages)

    @property
    def size(self) -> int:
        return 1 + sum([package_info.size for package_info in self.packages])

    def get_package_by_token(self, token: int) -> PackageInfo:
        assert token < self.count
        return self.packages[token]

    def get_token_by_package_aid(self, package_aid: str) -> int | None:
        package_aid = package_aid.lower()
        for token, package in enumerate(self.packages):
            if package.aid_hex == package_aid:
                return token
        return None

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ImportComponent:
        raw = raw[start_offset:]
        assert raw[0] == ImportComponent.tag

        count = raw[3]
        packages = []
        offset = 0
        for package_num in range(count):
            package_info = PackageInfo.load(cap_file, raw[4:], offset)
            offset += package_info.size
            packages.append(package_info)

        return ImportComponent(cap_file, packages)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(ImportComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        raw.append(self.count)
        for package_info in self.packages:
            raw.extend(package_info.to_bytes())
        return bytes(raw)

    def pretty_print(self) -> None:
        print("Import component")
        print()
        print("Packages:")
        for package_info in self.packages:
            print(textwrap.indent(str(package_info), "\t"))

# import_component = ImportComponent.load_from_file("../template_method/applets/javacard/Import.cap")
# # new_package_info = PackageInfo(12, 3, bytes.fromhex("a000ef"))
# # import_component.packages.append(new_package_info)
# # import_component.export_to_file("../Import.cap")
# # import_component = ImportComponent.load_from_file("../Import.cap")
# import_component.pretty_print()
