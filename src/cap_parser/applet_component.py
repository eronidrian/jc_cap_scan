from __future__ import annotations

import textwrap

from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags


class AppletComponent(Component):
    class Applet(Structure):

        def __init__(self, cap_file: CapFile, aid: bytes, install_method_offset: int):
            super().__init__(cap_file)
            self.aid = aid
            self.install_method_offset = install_method_offset

        @property
        def aid_length(self) -> int:
            return len(self.aid)

        @property
        def aid_hex(self) -> str:
            return self.aid.hex().lower()

        @property
        def size(self) -> int:
            return 1 + self.aid_length + 2

        @staticmethod
        def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> AppletComponent.Applet:
            raw = raw[start_offset:]

            aid_length = raw[0]
            aid = raw[1: 1 + aid_length]
            install_method_offset = int.from_bytes(raw[1 + aid_length: 1 + aid_length + 2])

            return AppletComponent.Applet(cap_file, aid, install_method_offset)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.aid_length)
            raw.extend(self.aid)
            raw.extend(int.to_bytes(self.install_method_offset, 2))

            return bytes(raw)

        def __str__(self):
            return (f"AID: {self.aid_hex}\n"
                    f"Install method offset: {self.install_method_offset}\n")

    tag = ComponentTags.COMPONENT_Applet
    filename = "Applet.cap"

    def __init__(self, cap_file: CapFile, applets: list[Applet]):
        super().__init__(cap_file)
        self.applets = applets

    @property
    def count(self) -> int:
        return len(self.applets)

    def __str__(self):
        result_string = "Applet component\n\n"
        result_string += "Applets:\n"
        for applet in self.applets:
            result_string += textwrap.indent(str(applet), "\t") + "\n"
        return result_string

    def pretty_print(self) -> None:
        print(self.__str__())

    @property
    def size(self) -> int:
        return 1 + Utils.size_of_structure_array(self.applets)


    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> AppletComponent:
        raw = raw[start_offset:]
        assert raw[0] == AppletComponent.tag

        count = raw[3]
        _, applets = Utils.load_structure_array(cap_file, raw, 4, count, AppletComponent.Applet)

        return AppletComponent(cap_file, applets)

    def to_bytes(self) -> bytearray:
        raw = super().to_bytes()
        raw.append(self.count)
        for applet in self.applets:
            raw.extend(applet.to_bytes())
        return raw
