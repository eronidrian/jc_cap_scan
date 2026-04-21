import argparse
import os.path
import shutil
import sys

from cap_parser.cap_file import CapFile
from cap_parser.constant_pool_component import CpInfo
from cap_parser.import_component import PackageInfo, ImportComponent
from jc_cap_scan.utils.cap_file_utils import pack_directory_to_cap_file


def format_import_component(cap_file: CapFile, package_aid: bytearray, major: int, minor: int) -> CapFile:
    javacard_framework_package_info = PackageInfo(cap_file, 3, 1, b'\xA0\x00\x00\x00\x62\x01\x01')
    target_package_info = PackageInfo(cap_file, minor, major, package_aid)
    cap_file.import_component = ImportComponent(cap_file, [javacard_framework_package_info, target_package_info])

    return cap_file


def format_constant_pool_component(cap_file: CapFile, class_token: int, cp_info_type: int) -> CapFile:
    cap_file.constant_pool_component.constant_pool[-1] = CpInfo.load(cap_file, bytearray([cp_info_type, 129, class_token, 0]))
    return cap_file

def generate_cap_for_package_aid(package_aid: bytearray, major: int, minor: int, template_directory: str, output: str) -> str:
    cap_file = CapFile.load_from_directory(os.path.join(template_directory, "test", "javacard"))
    cap_file = format_import_component(cap_file, package_aid, major, minor)

    cap_file.export_to_directory(os.path.join("tmp", "test", "javacard"))
    pack_directory_to_cap_file(output, "tmp")
    shutil.rmtree("tmp")
    return output


def generate_cap_for_package_aid_and_class_token(package_aid: bytearray, major: int, minor: int, template_directory: str, class_token: int, cp_info_type: int, output: str) -> str:
    cap_file = CapFile.load_from_directory(os.path.join(template_directory, "test", "javacard"))
    cap_file = format_import_component(cap_file, package_aid, major, minor)
    cap_file = format_constant_pool_component(cap_file, class_token, cp_info_type)

    cap_file.export_to_directory(os.path.join("tmp", "test", "javacard"))
    pack_directory_to_cap_file(output, "tmp")
    shutil.rmtree("tmp")
    return output

def main():
    parser = argparse.ArgumentParser(
        prog="Generate CAP files"
    )

    parser.add_argument('--aid', help="Package AID", required=True)
    parser.add_argument('--major', help="Major version of the package", required=False, type=int, default=1)
    parser.add_argument("--minor", help="Minor version of the package", required=False, type=int, default=0)
    parser.add_argument("--class_token", help="Class token", required=False, type=int)
    parser.add_argument("--cp_info", help="CP Info type for the class entry in Constant pool",
                        required='--class_token' in sys.argv[1], type=int)
    parser.add_argument("--template", help="Directory with the template", required=False,
                        default="templates/generic_template")
    parser.add_argument("--output", help="Output CAP file location", required=True)

    args = parser.parse_args()

    if args.class_token is None:
        generate_cap_for_package_aid(bytearray.fromhex(args.aid), args.major, args.minor, args.template, args.output)
    else:
        generate_cap_for_package_aid_and_class_token(bytearray.fromhex(args.aid), args.major, args.minor, args.template,
                                                     args.class_tolken, args.cp_info, args.output)


if __name__ == '__main__':
    main()