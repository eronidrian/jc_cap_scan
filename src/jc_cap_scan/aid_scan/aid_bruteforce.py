import csv
import os

from jc_cap_scan.config.config import MeasurementConfig, Config
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.measurement_utils import measure_cap_file_install
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file



def do_dummy_measurements(traces_directory: str, num_of_dummy_measurements: int, config: MeasurementConfig, auth: list[str] | None = None):
    if num_of_dummy_measurements == 0:
        return

    base_aid = bytearray.fromhex("ff" * 7)
    base_major, base_minor = (1, 0)
    cap_file_name = generate_cap_for_package_aid(base_aid, base_major, base_minor, os.path.join("templates", "generic_template"),
                                                 f'bruteforce_{base_aid.hex()}.cap')
    for i in range(num_of_dummy_measurements):
        print(f"{i + 1}/{num_of_dummy_measurements}")
        measure_cap_file_install(cap_file_name, 1, os.path.join(traces_directory, "dummy.trs"), config, auth)
    os.remove(cap_file_name)
    os.remove(os.path.join(traces_directory, "dummy.trs"))


def aid_bruteforce(num_of_dummy_measurements: int, result_file_name: str, base_aid: str, byte_numbers: list[int],
                   base_major: int, base_minor: int, measurements_for_one_byte: int, traces_directory: str, config: Config, auth: list[str] | None, tidy_up: bool = False):

    print("PERFORMING DUMMY MEASUREMENTS")
    do_dummy_measurements(traces_directory, num_of_dummy_measurements, config.measurement, auth)

    print("STARTING MEASUREMENT")
    result_file = open(result_file_name, "w")
    result_file_writer = csv.writer(result_file)
    base_aid = bytearray.fromhex(base_aid)

    for byte_number in byte_numbers:
        for byte_value in range(256):
            current_aid = base_aid.copy()
            current_aid[byte_number] = byte_value
            print(f"Measuring: {current_aid.hex()}")
            cap_file_name = generate_cap_for_package_aid(current_aid, base_major, base_minor, 'templates/template_generic', f'bruteforce_{current_aid.hex()}.cap')
            measure_cap_file_install(cap_file_name, measurements_for_one_byte, os.path.join(traces_directory, f'bruteforce_{base_aid.hex()}.trs'), config.measurement, auth)
            times = extract_times_from_trs_file(os.path.join(traces_directory, f'bruteforce_{base_aid.hex()}.trs'), config.extraction)
            result_file_writer.writerow([byte_number, byte_value] + times)
            if tidy_up:
                os.remove(cap_file_name)
                os.path.join(traces_directory, f'bruteforce_{base_aid.hex()}.trs')


