import os.path

from cap_parser.cap_file import CapFile
from cap_parser.constant_pool_component import CpInfo
from cap_parser.import_component import PackageInfo, ImportComponent
from utils.cap_file_utils import pack_directory_to_cap_file


def format_import_component(cap_file: CapFile, package_aid: bytearray, major: int, minor: int):
    javacard_framework_package_info = PackageInfo(cap_file, 0, 1, b'\xA0\x00\x00\x00\x62\x01\x01')
    target_package_info = PackageInfo(cap_file, minor, major, package_aid)
    cap_file.import_component = ImportComponent(cap_file, [javacard_framework_package_info, target_package_info])

    return cap_file


def format_constant_pool_component(cap_file: CapFile, class_token: int, cp_info_type: int):
    cap_file.constant_pool_component.constant_pool[-1] = CpInfo.load(cap_file, bytearray([cp_info_type, 129, class_token, 0]))
    return cap_file

def generate_cap_for_package_aid(package_aid: bytearray, major: int, minor: int, template_directory: str, output: str):
    cap_file = CapFile.load_from_directory(os.path.join(template_directory, "test", "javacard"))
    cap_file = format_import_component(cap_file, package_aid, major, minor)

    cap_file.export_to_directory("tmp")
    pack_directory_to_cap_file(output, "tmp")


def generate_cap_for_package_aid_and_class_token(package_aid: bytearray, major: int, minor: int, template_directory: str, class_token: int, cp_info_type: int, output: str):
    cap_file = CapFile.load_from_directory(os.path.join(template_directory, "test", "javacard"))
    cap_file = format_import_component(cap_file, package_aid, major, minor)
    cap_file = format_constant_pool_component(cap_file, class_token, cp_info_type)

    cap_file.export_to_directory("tmp")
    pack_directory_to_cap_file(output, "tmp")

