import csv
import os

from jc_cap_scan.utils.cap_file_utils import is_installation_successful
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid_and_class_token


def class_bruteforce(result_file: str, class_token_range: tuple[int, int], base_aid: bytearray, major: int, minor: int, cp_info_type: int,
                     tidy_up: bool, auth: list[str] | None = None):

    f = open(result_file, "w")
    result_writer = csv.writer(f)

    for class_token in range(class_token_range[0], class_token_range[1]):
        cap_name = generate_cap_for_package_aid_and_class_token(base_aid, major, minor, "templates/generic_template", class_token, cp_info_type, f"class_{base_aid.hex()}_{class_token}.cap")
        success, _ = is_installation_successful(cap_name, auth)
        result_writer.writerow([class_token, success])
        if tidy_up:
            os.remove(cap_name)


