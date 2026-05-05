import argparse
import csv
import os
from typing import Literal

from jc_cap_scan.utils.cap_file_utils import is_installation_successful
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid_and_class_token


def class_bruteforce(results_file: str, class_token_range: tuple[int, int], base_aids: list[str], base_major: int,
                     base_minor: int, cp_info_type: Literal['class', 'method'],
                     tidy_up: bool, auth: list[str] | None = None):
    """
    Bruteforce class tokens without capturing power traces
    :param results_file: Path, where to save the results of the test
    :param class_token_range: Range of class tokens to test
    :param base_aids: AIDs to use as a base for the testing, in hex format
    :param base_major: Base major version to use for the testing
    :param base_minor: Base minor version to use for the testing
    :param cp_info_type: Type of cpInfo to use to reference the class token in the generated CAP files. Either 'class' for ClassRef or 'method' for StaticMethodRef
    :param tidy_up: Where to tidy up the generated CAP files
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    assert cp_info_type in ['static', 'class']
    f = open(results_file, "w")
    result_writer = csv.writer(f)
    print("Starting measurement...")

    for base_aid in base_aids:
        print(f"Testing AID {base_aid}")
        for class_token in range(class_token_range[0], class_token_range[1]):
            print(
                f"Class token {class_token - class_token_range[0]}/{class_token_range[1] - class_token_range[0]} ({class_token})")
            cp_info_number = 1 if cp_info_type == 'class' else 6
            cap_name = f"class_{base_aid}_{class_token}.cap"
            generate_cap_for_package_aid_and_class_token(bytearray.fromhex(base_aid),
                                                         base_major,
                                                         base_minor,
                                                         "templates/generic_template",
                                                         class_token,
                                                         cp_info_number,
                                                         cap_name)
            success, response = is_installation_successful(cap_name, auth)
            result_writer.writerow([class_token, success])
            if tidy_up:
                os.remove(cap_name)

            print(f"Class token: {class_token}\n"
                  f"Response: {response}\n"
                  f"Success: {success}")

def main():
    parser = argparse.ArgumentParser(
        prog="Class bruteforce"
    )

    parser.add_argument('--class_token_range', help="Range of class tokens to test, e.g. 0 255",
                                   required=False, nargs=2, default=(0, 255), type=int)
    parser.add_argument('-a', '--base_aid', help="AID(s) in hex to use as a base for the testing",
                                   required=True, nargs='+')
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--cp_info_type',
                                   help="cpInfo type to use for testing. class - Classref, method - Staticmethodref",
                                   required=False, type=str, default='class')
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    class_bruteforce(args.results_file, args.class_token_range, args.base_aid, args.major, args.minor,
                     args.cp_info_type, args.tidy_up, args.auth)


if __name__ == '__main__':
    main()
