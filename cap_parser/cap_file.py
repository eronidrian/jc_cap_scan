from __future__ import annotations

import os.path

from cap_parser.applet_component import AppletComponent
from cap_parser.class_component import ClassComponent
from cap_parser.directory_component import DirectoryComponent
from cap_parser.header_component import HeaderComponent
from cap_parser.import_component import ImportComponent


class CapFile:


    def __init__(self, header_component: HeaderComponent = None, directory_component: DirectoryComponent = None, import_component: ImportComponent = None, applet_component: AppletComponent = None, class_component: ClassComponent = None):
        self.header_component = header_component
        self.directory_component = directory_component
        self.import_component = import_component
        self.applet_component = applet_component
        self.class_component = class_component

    @staticmethod
    def load_from_directory(directory_name: str) -> CapFile:
        cap_file = CapFile()
        cap_file.header_component = HeaderComponent.load_from_file(cap_file, os.path.join(directory_name, HeaderComponent.filename))
        cap_file.directory_component = DirectoryComponent.load_from_file(cap_file, os.path.join(directory_name, DirectoryComponent.filename))
        cap_file.import_component = ImportComponent.load_from_file(cap_file, os.path.join(directory_name, ImportComponent.filename))
        cap_file.applet_component = AppletComponent.load_from_file(cap_file, os.path.join(directory_name, AppletComponent.filename))
        cap_file.class_component = ClassComponent.load_from_file(cap_file, os.path.join(directory_name, ClassComponent.filename))

        return cap_file

cap_file = CapFile.load_from_directory("../simple_applet/applets/javacard")
cap_file.class_component.pretty_print()