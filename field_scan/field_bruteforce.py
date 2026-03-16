import csv
import os
import shutil

from cap_parser.cap_file import CapFile
from cap_parser.constant_pool_component import CpInfo
from cap_parser.import_component import PackageInfo
from utils.cap_file_utils import is_installation_successful, pack_directory_to_cap_file


def field_bruteforce(result_file: str, field_token_range: tuple[int, int], base_aid: bytearray, major: int, minor: int, base_class_token: int, cp_info_type: int,
                     tidy_up: bool, auth: list[str] | None = None):

    f = open(result_file, "w")
    result_writer = csv.writer(f)

    for field_token in range(field_token_range[0], field_token_range[1]):
        cap_file = CapFile.load_from_directory("../templates/generic_template/test/javacard")
        cap_file.import_component.packages[1] = PackageInfo(cap_file, minor, major, base_aid)
        cap_file.constant_pool_component.constant_pool.append(CpInfo.load(cap_file, bytearray([cp_info_type, 129, base_class_token, field_token])))
        cap_file.export_to_directory(os.path.join(f"../field_{base_class_token}_{field_token}", "test", "javacard"))
        cap_name = f"../field_{base_class_token}_{field_token}.cap"
        pack_directory_to_cap_file(cap_name, f"../field_{base_class_token}_{field_token}")

        success, response = is_installation_successful(cap_name, auth)
        print(response)
        result_writer.writerow([field_token, success])
        if tidy_up:
            os.remove(cap_name)
            shutil.rmtree(f"../field_{base_class_token}_{field_token}")


if __name__ == '__main__':
    field_bruteforce("test.csv", (0, 256), bytearray.fromhex("A0000000620102"), 1, 0, 13, 2, True)


