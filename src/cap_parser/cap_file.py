from __future__ import annotations

import os.path
import sys
from difflib import context_diff
from typing import Iterator

from cap_parser.applet_component import AppletComponent
from cap_parser.class_component import ClassComponent
from cap_parser.component import Component
from cap_parser.constant_pool_component import ConstantPoolComponent
from cap_parser.descriptor_component import DescriptorComponent
from cap_parser.directory_component import DirectoryComponent
from cap_parser.header_component import HeaderComponent
from cap_parser.import_component import ImportComponent
from cap_parser.method_component import MethodComponent
from cap_parser.reference_location_component import ReferenceLocationComponent
from cap_parser.static_field_component import StaticFieldComponent


class CapFile:
    components_install_order = [
        ("header_component", HeaderComponent),
        ("directory_component", DirectoryComponent),
        ("import_component", ImportComponent),
        ("applet_component", AppletComponent),
        ("class_component", ClassComponent),
        ("method_component", MethodComponent),
        ("static_field_component", StaticFieldComponent),
        ("constant_pool_component", ConstantPoolComponent),
        ("reference_location_component", ReferenceLocationComponent),
        # ("descriptor_component", DescriptorComponent),
    ]

    components_standard_order = [
        ("header_component", HeaderComponent),
        ("directory_component", DirectoryComponent),
        ("applet_component", AppletComponent),
        ("import_component", ImportComponent),
        ("constant_pool_component", ConstantPoolComponent),
        ("class_component", ClassComponent),
        ("method_component", MethodComponent),
        ("static_field_component", StaticFieldComponent),
        ("reference_location_component", ReferenceLocationComponent),
    ]

    def __init__(self):
        # only because of PyCharm suggestions
        self.header_component: HeaderComponent = None
        self.directory_component: DirectoryComponent = None
        self.import_component: ImportComponent = None
        self.applet_component: AppletComponent = None
        self.class_component: ClassComponent = None
        self.method_component: MethodComponent = None
        self.static_field_component: StaticFieldComponent = None
        self.constant_pool_component: ConstantPoolComponent = None
        self.reference_location_component: ReferenceLocationComponent = None
        self.descriptor_component: DescriptorComponent = None

        # for attr, _ in self.components:
        #     setattr(self, attr, None)

    @classmethod
    def load_from_directory(cls, directory_name: str) -> CapFile:
        cap_file = cls()
        for attr, component_class in cls.components_install_order:
            component = component_class.load_from_file(cap_file, os.path.join(directory_name, component_class.filename))
            setattr(cap_file, attr, component)
        return cap_file

    def __str__(self):
        result_string = ""
        for attr, _ in self.components_install_order:
            component = getattr(self, attr)
            result_string += str(component)
            result_string += "-" * 50 + "\n"
        return result_string

    def get_components_in_standard_order(self) -> Iterator[Component]:
        for attr, _ in self.components_standard_order:
            component = getattr(self, attr)
            yield component

    def pretty_print(self) -> None:
        print(self.__str__())


    def export_to_directory(self, directory_name: str) -> None:
        os.makedirs(directory_name, exist_ok=True)
        for attr, _ in self.components_install_order:
            component = getattr(self, attr)
            component.export_to_file(os.path.join(directory_name, component.filename))

    @staticmethod
    def diff(cap_file_1: CapFile, cap_file_2: CapFile) -> None:
        cap_file_1_lines = []
        for line in str(cap_file_1).splitlines(keepends=True):
            if line == "\n" or "-" * 50 in line:
                continue
            line = line.replace("\t", "")
            cap_file_1_lines.append(line)


        cap_file_2_lines = []
        for line in str(cap_file_2).splitlines(keepends=True):
            if line == "\n" or "-" * 50 in line:
                continue
            line = line.replace("\t", "")
            cap_file_2_lines.append(line)

        difference = context_diff(cap_file_1_lines, cap_file_2_lines, fromfile="CAP file 1", tofile="CAP file 2")

        sys.stdout.writelines(difference)

if __name__ == "__main__":
    cap_file = CapFile.load_from_directory("../simple_applet/applets/javacard")
    cap_file.pretty_print()
    cap_file.export_to_directory("../test_export")
