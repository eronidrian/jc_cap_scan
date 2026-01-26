from __future__ import annotations

import textwrap

from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils

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
        package_from_api = API_SPECIFICATION.get_package_by_aid(self.aid_hex)
        package_name = package_from_api.name if package_from_api is not None else "not found in JC API"
        return (f"AID: {self.aid_hex} ({package_name})\n"
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
        return 1 + Utils.size_of_structure_array(self.packages)

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
        _, packages = Utils.load_structure_array(cap_file, raw, 4, count, PackageInfo)

        return ImportComponent(cap_file, packages)

    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        raw.append(self.count)
        for package_info in self.packages:
            raw.extend(package_info.to_bytes())
        return bytes(raw)

    def __str__(self):
        result_string = "Import Component\n\n"
        result_string += "Packages:\n"
        for package_info in self.packages:
            result_string += textwrap.indent(str(package_info), "\t") + "\n"
        return result_string

    def pretty_print(self) -> None:
        print(self.__str__())
