import argparse
import csv
import os
import shutil
import sys
from typing import Literal

from cap_parser.cap_file import CapFile
from cap_parser.constant_pool_component import CpInfo
from cap_parser.import_component import PackageInfo
from jc_cap_scan.utils.cap_file_utils import is_installation_successful, pack_directory_to_cap_file


def field_bruteforce(result_file: str, field_token_range: tuple[int, int], base_aids: list[str], base_major: int, base_minor: int, class_token_range: tuple[int, int], field_type: Literal['static', 'virtual'],
                     tidy_up: bool, auth: list[str] | None = None):

    f = open(result_file, "w")
    result_writer = csv.writer(f)

    cap_file = CapFile.load_from_directory("templates/generic_template/test/javacard")

    print("Starting measurement...")
    for base_aid in base_aids:
        print(f"Testing {base_aid}")
        for class_token in range(class_token_range[0], class_token_range[1]):
            print(f"Testing {class_token}")
            for field_token in range(field_token_range[0], field_token_range[1]):
                print(
                    f"Field token {field_token - field_token_range[0]}/{field_token_range[1] - field_token_range[0]} ({field_token})")

                cap_file.import_component.packages[1] = PackageInfo(cap_file, base_minor, base_major, bytes.fromhex(base_aid))
                if field_type == "static":
                    cap_file.constant_pool_component.constant_pool[-1] = CpInfo.load(cap_file, bytearray([5, 129, class_token, field_token]))
                elif field_type == "virtual":
                    cap_file.constant_pool_component.constant_pool[-1] = CpInfo.load(cap_file, bytearray([2, 129, class_token, field_token]))
                cap_file.export_to_directory(os.path.join(f"field_{base_aid}_{class_token}_{field_token}", "test", "javacard"))
                cap_name = f"field_{base_aid}_{class_token}_{field_token}.cap"
                pack_directory_to_cap_file(cap_name, f"field_{base_aid}_{class_token}_{field_token}")

                success, response = is_installation_successful(cap_name, auth)
                result_writer.writerow([field_token, success])
                if tidy_up:
                    os.remove(cap_name)
                    shutil.rmtree(f"field_{base_aid}_{class_token}_{field_token}")

                print(f"AID: {base_aid}\n"
                      f"Class token: {class_token}\n"
                      f"Field token: {field_token}\n"
                      f"Response: {response}\n"
                      f"Success: {success}")

def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="Field bruteforce"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--field_token_range', help="Range of field tokens to test, e.g. 0 255",
                        required=False, nargs=2, default=(0, 255), type=int)
    parser.add_argument('-a', '--base_aid', help="AID(s) in hex to use as a base for the testing",
                                   required=True, nargs='+')
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument("--class_token_range", help="Class token range to test, e.g. 0 255", type=int, nargs=2, required=True)
    parser.add_argument('--field_type',
                        help="Field type to use for testing. 'static' or 'virtual'",
                        required=True, type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args(argv)

    field_bruteforce(args.results_file, args.field_token_range, args.base_aid, args.major, args.minor, args.class_token, args.field_type, args.tidy_up, args.auth)


if __name__ == '__main__':
    main(sys.argv[1:])

