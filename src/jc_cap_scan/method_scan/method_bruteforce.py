import argparse
import csv
import shutil
import os

from cap_parser.cap_file import CapFile
from jc_cap_scan.utils.cap_file_utils import uninstall, pack_directory_to_cap_file, install, call, reset_fault_counter


def is_template_correct(template_location: str, auth: list[str] | None = None) -> bool:
    """
    Check whether the given template is correct. Correct template should be installable and callable
    :param template_location: Path to the template file
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return: True if template is correct, False otherwise
    """
    cap_name = "template_test.cap"
    pack_directory_to_cap_file(cap_name, template_location)

    install_response = install(cap_name, auth)
    if "CAP loaded" not in install_response:
        print(f"Template {template_location} did not install successfully")
        print(f"Response: {install_response}")
        return False

    call_response = call(debug=True, auth=auth)
    if "9000" not in call_response:
        print(f"Template {template_location} cannot be called successfully")
        print(f"Response: {call_response}")
        return False

    uninstall(cap_name, auth)
    os.remove(cap_name)
    return True


def method_bruteforce(results_file: str, method_token_range: tuple[int, int], template_number: int, tidy_up: bool,
                      auth: list[str] | None = None) -> None:
    """
    Bruteforce method tokens without capturing power trace
    :param results_file: Path to file where to store the results
    :param method_token_range: Range of method tokens to test
    :param template_number: Use template with given number, -1 if all templates should be used
    :param tidy_up: Whether to delete the generated CAP files
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    uninstall("templates/good_package.cap")
    f = open(results_file, "w")
    csv_writer = csv.writer(f)
    for i, entry in enumerate(sorted(os.scandir("templates/method_templates"), key=lambda ent: ent.name)):
        if not entry.is_dir():
            continue

        # if a template number is specified skip all other templates
        if template_number != -1 and i != template_number:
            continue

        _, _, static_or_virtual, class_name, method_name, return_or_call = entry.name.split("_")
        print(f"Testing template {entry.name}")
        if not is_template_correct(entry.path):
            print(f"Skipping template {entry.name}")
            continue
        print("Template is correct")

        template_loaded = CapFile.load_from_directory(os.path.join(entry.path, "applets", "javacard"))
        constant_pool_entry = template_loaded.constant_pool_component.get_cp_info_by_method_name(method_name)
        for method_token in range(method_token_range[0], method_token_range[1]):
            # modify method token in the ConstantPool component
            constant_pool_entry.info.token = method_token
            template_loaded.export_to_directory(os.path.join(f"{entry.name}_{method_token}", "applets", "javacard"))
            cap_file_name = f"{entry.name}_{method_token}.cap"
            pack_directory_to_cap_file(cap_file_name, f"{entry.name}_{method_token}")

            install_response = install(cap_file_name, auth)
            call_response = ""
            if "CAP loaded" in install_response:
                call_response = call()

            print(f"{method_token} - {install_response} - {call_response}")
            csv_writer.writerow([entry.name, method_token, install_response, call_response])
            uninstall(cap_file_name, auth)

            if method_token % 5 == 0:
                print("Resetting fault counter...")
                reset_fault_counter(auth)
            if tidy_up:
                os.remove(cap_file_name)
                shutil.rmtree(f"{entry.name}_{method_token}")


def main():
    parser = argparse.ArgumentParser(
        prog="Method bruteforce"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--template_number', help="Template CAP file number to use", required=False, default=-1,
                                    type=int)
    parser.add_argument('--method_token_range', help="Range of method tokens to test, e.g. 0 255",
                                    required=False, nargs=2, default=(0, 255), type=int)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    method_bruteforce(args.results_file, args.method_token_range, args.template_number, args.tidy_up, args.auth)


if __name__ == '__main__':
    main()

