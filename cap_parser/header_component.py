from __future__ import annotations

import textwrap

from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component
from cap_parser.constants import ComponentTags
from cap_parser.import_component import PackageInfo


class HeaderComponent(Component):
    magic = bytes.fromhex("DECAFFED")
    tag = ComponentTags.COMPONENT_Header
    filename = "Header.cap"

    flag_masks = {
        "ACC_INT": 0x01,
        "ACC_EXPORT": 0x02,
        "ACC_APPLET": 0x04,
        "ACC_EXTENDED": 0x08
    }

    def __init__(self, cap_file: CapFile, cap_format_minor_version: int, cap_format_major_version: int, flags: int, package: PackageInfo):
        super().__init__(cap_file)
        self.cap_format_minor_version = cap_format_minor_version
        self.cap_format_major_version = cap_format_major_version
        self.flags = flags
        self.package = package

    @property
    def flags_str(self) -> str:
        flags_str = []
        for flag_name in HeaderComponent.flag_masks:
            if Utils.is_flag_set(self.flags, HeaderComponent.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)


    def pretty_print(self) -> None:
        print("Header component")
        print()
        print(f"CAP format minor version: {self.cap_format_minor_version}")
        print(f"CAP format major version: {self.cap_format_major_version}")
        print(f"Flags: {self.flags} ({self.flags_str})")
        print("Package:")
        print(textwrap.indent(str(self.package), "\t"))

    @property
    def size(self) -> int:
        return 7 + self.package.size

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> HeaderComponent:
        raw = raw[start_offset:]
        assert raw[0] == HeaderComponent.tag
        assert raw[3:7] == HeaderComponent.magic
        cap_format_minor_version = raw[7]
        cap_format_major_version = raw[8]
        flags = raw[9]
        package = PackageInfo.load(cap_file, raw[10:], 0)
        return HeaderComponent(cap_file, cap_format_minor_version, cap_format_major_version, flags, package)

    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        raw.extend(HeaderComponent.magic)
        raw.append(self.cap_format_minor_version)
        raw.append(self.cap_format_major_version)
        raw.append(self.flags)
        raw.extend(self.package.to_bytes())

        return bytes(raw)
