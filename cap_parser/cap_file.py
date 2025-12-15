from __future__ import annotations

import os.path

from cap_parser.applet_component import AppletComponent
from cap_parser.class_component import ClassComponent
from cap_parser.constant_pool_component import ConstantPoolComponent
from cap_parser.descriptor_component import DescriptorComponent
from cap_parser.directory_component import DirectoryComponent
from cap_parser.header_component import HeaderComponent
from cap_parser.import_component import ImportComponent
from cap_parser.method_component import MethodComponent
from cap_parser.reference_location_component import ReferenceLocationComponent
from cap_parser.static_field_component import StaticFieldComponent


class CapFile:
    components = [
        ("header_component", HeaderComponent),
        ("directory_component", DirectoryComponent),
        ("import_component", ImportComponent),
        ("applet_component", AppletComponent),
        ("class_component", ClassComponent),
        ("method_component", MethodComponent),
        ("static_field_component", StaticFieldComponent),
        ("constant_pool_component", ConstantPoolComponent),
        ("reference_location_component", ReferenceLocationComponent),
        ("descriptor_component", DescriptorComponent),
    ]

    def __init__(self):
        # only because of Pycharm suggestions
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
        for attr, component_class in cls.components:
            component = component_class.load_from_file(cap_file, os.path.join(directory_name, component_class.filename))
            setattr(cap_file, attr, component)
        return cap_file

    def pretty_print(self) -> None:
        for attr, _ in self.components:
            component = getattr(self, attr)
            component.pretty_print()
            print("-" * 50)


    def export_to_directory(self, directory_name: str) -> None:
        os.makedirs(directory_name, exist_ok=True)
        for attr, _ in self.components:
            component = getattr(self, attr)
            component.export_to_file(os.path.join(directory_name, component.filename))


if __name__ == "__main__":
    cap_file = CapFile.load_from_directory("../simple_applet/applets/javacard")
    cap_file.pretty_print()
    cap_file.export_to_directory("../test_export")
