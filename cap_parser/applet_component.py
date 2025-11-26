from __future__ import annotations

import textwrap

from packaging.tags import android_platforms

from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags


class AppletComponent(Component):
    class Applet(Structure):

        def __init__(self, aid: bytes, install_method_offset: int):
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
        def load(raw: bytes, start_offset: int = 0) -> AppletComponent.Applet:
            raw = raw[start_offset:]

            aid_length = raw[0]
            aid = raw[1: 1 + aid_length]
            install_method_offset = int.from_bytes(raw[1 + aid_length: 1 + aid_length + 2])

            return AppletComponent.Applet(aid, install_method_offset)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.aid_length)
            raw.extend(self.aid)
            raw.extend(int.to_bytes(self.install_method_offset, 2))

            return bytes(raw)

        def __str__(self):
            return (f"AID: {self.aid_hex}\n"
                    f"Install method offset: {self.install_method_offset}\n")

    tag = ComponentTags.Component_Applet

    def __init__(self, applets: list[Applet]):
        self.applets = applets

    @property
    def count(self) -> int:
        return len(self.applets)

    def pretty_print(self) -> None:
        print("Applet component")
        print()
        print("Applets:")
        for applet in self.applets:
            print(textwrap.indent(str(applet), "\t"))

    @property
    def size(self) -> int:
        return 1 + sum([applet.size for applet in self.applets])


    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> AppletComponent:
        raw = raw[start_offset:]
        assert raw[0] == AppletComponent.tag

        count = raw[3]
        offset = 0
        applets = []
        for _ in range(count):
            applet = AppletComponent.Applet.load(raw[4:], offset)
            offset += applet.size
            applets.append(applet)

        return AppletComponent(applets)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(AppletComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        raw.append(self.count)
        for applet in self.applets:
            raw.extend(applet.to_bytes())
        return bytes(raw)

applet_component = AppletComponent.load_from_file("../template_method/applets/javacard/Applet.cap")
applet_component.export_to_file("../Applet.cap")
applet_component = AppletComponent.load_from_file("../Applet.cap")
applet_component.pretty_print()
