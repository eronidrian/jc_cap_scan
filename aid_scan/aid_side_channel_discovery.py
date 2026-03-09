import csv
import random
import os

from aid_scan.aid_bruteforce import do_dummy_measurements
from config import Config
from trs_analysis.trs_extractor import extract_times_from_trs_file
from utils.cap_manipulation_utils import generate_cap_for_package_aid
from utils.measurement_utils import measure_cap_file_install


def aid_side_channel_discovery(num_of_dummy_measurements: int, result_file_name: str, base_aids: list[str], byte_numbers: list[int],
                   base_major: int, base_minor: int, measurements_for_one_cap_file: int, traces_directory: str, changed_byte_values: list[int], config: Config, auth: list[str] | None, tidy_up: bool = False):

    print("PERFORMING DUMMY MEASUREMENTS")
    do_dummy_measurements(traces_directory, num_of_dummy_measurements, config.measurement, auth)

    print("STARTING MEASUREMENT")
    result_file = open(result_file_name, "w")
    result_file_writer = csv.writer(result_file)

    results = {}

    for base_aid in base_aids:
        base_aid = bytearray.fromhex(base_aid)
        for changed_byte_value in changed_byte_values:
            random_byte_order = byte_numbers
            random.shuffle(random_byte_order)
            for changed_byte_number in random_byte_order:
                aid_modified = base_aid.copy()
                aid_modified[changed_byte_number] = changed_byte_value
                cap_file_name = f"test_{aid_modified.hex()}.cap"
                generate_cap_for_package_aid(aid_modified, base_major, base_minor, "templates/template_generic",
                                             cap_file_name)
                measure_cap_file_install(cap_file_name, measurements_for_one_cap_file,
                                         os.path.join(traces_directory, f"test_{aid_modified.hex()}.trs"),
                                         config.measurement, auth)
                times = extract_times_from_trs_file(measurements_for_one_cap_file,
                                                    os.path.join(traces_directory, f'test_{base_aid.hex()}.trs'), config.measurement.number_of_samples, config.extraction)

                if results.get(changed_byte_number) is None:
                    results[changed_byte_number] = []
                results[changed_byte_number].extend(times)

                if tidy_up:
                    os.remove(cap_file_name)
                    os.path.join(traces_directory, f'test_{base_aid.hex()}.trs')

    for changed_byte_number in sorted(list(results.keys())):
        result_file_writer.writerow([changed_byte_number] + results[changed_byte_number])
