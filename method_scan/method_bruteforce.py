import csv
import shutil
import os

from cap_parser.cap_file import CapFile
from utils.cap_file_utils import uninstall, pack_directory_to_cap_file, install, call, reset_fault_counter


def is_template_correct(template_location: str, auth: list[str] | None = None) -> bool:
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


def method_bruteforce(result_file: str, tidy_up: bool, template_number: int | None = None, method_token_range: tuple[int, int] = (0, 256), auth: list[str] | None = None) -> None:
    uninstall("templates/good_package.cap")
    f = open(result_file, "w")
    csv_writer = csv.writer(f)
    for i, entry in enumerate(sorted(os.scandir("templates/method_templates"), key=lambda ent: ent.name)):
        if not entry.is_dir():
            continue

        if template_number is not None and i != template_number:
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

