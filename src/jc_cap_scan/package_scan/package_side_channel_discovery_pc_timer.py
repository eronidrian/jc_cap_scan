import argparse
import csv
import random
import os
import re
import subprocess
import time
from _csv import Writer


from jc_cap_scan.utils.cap_file_utils import install
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid


def measure_time_full(cap_name: str, auth: list[str] | None = None) -> float:
    """
    Measure time of the whole installation process of the CAP file using PC timer.
    :param cap_name: Path to the CAP file
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :return: Duration of the installation process in nanoseconds
    """
    start = time.perf_counter_ns()
    install(cap_name, auth)
    end = time.perf_counter_ns()
    return end - start

def measure_time_load(cap_name: str, auth: list[str] | None = None) -> float | None:
    """
    Measure only the duration of the LOAD command processing using the PC timer
    :param cap_name: Path to the CAP file
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :return: Duration of the LOAD command processing, None if the time is not found in GP output
    """
    if auth is not None:
        result = subprocess.run(["java", "-jar", "src/jc_cap_scan/utils/gp_precise.jar", "--install",
                                 cap_name, "-d"] + auth,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        result = subprocess.run(["java", "-jar", "src/jc_cap_scan/utils/gp_precise.jar", "--install",
                                 cap_name, "-d"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    result = result.stdout.decode("utf-8")

    gp_log = result.splitlines()
    load_line = gp_log[23]
    match = re.search(r'([0-9]+)ns', load_line)
    if match is None:
        return None
    return float(match.group(1))


def test_single_changed_byte(results_writer: Writer, base_aid: bytearray, byte_number: int | None, byte_value: int | None,
                             major: int, minor: int, num_of_measurements: int, measure_load: bool,
                             tidy_up: bool, auth: list[str] | None = None):
    aid_modified = base_aid.copy()
    if byte_number is not None and byte_value is not None:
        aid_modified[byte_number] = byte_value

    cap_name = f"test_{aid_modified.hex()}_{major}_{minor}.cap"
    generate_cap_for_package_aid(aid_modified, major, minor, os.path.join("templates", "generic_template"),
                                 cap_name)
    times = []
    for i in range(num_of_measurements):
        print(f"Measurement {i + 1}/{num_of_measurements}")
        if measure_load:
            duration = measure_time_load(cap_name, auth)
        else:
            duration = measure_time_full(cap_name, auth)
        print(duration)
        times.append(duration)

    results_writer.writerow([base_aid.hex(), byte_number, major, minor] + times)

    if tidy_up:
        os.remove(cap_name)


def package_side_channel_discovery_pc_timer(results_file: str, base_aids: list[str],
                                            byte_numbers_to_test: list[int], base_major: int, base_minor: int,
                                            measurements_for_one_cap: int, measure_load: bool,
                                            values_for_changed_bytes: list[int], test_major: bool, test_minor: bool,
                                            tidy_up: bool, auth: list[str] | None = None):
    print("Starting measurement...")
    f = open(results_file, "w")
    result_writer = csv.writer(f)


    for i, base_aid in enumerate(base_aids):
        print(f"AID {i + 1}/{len(base_aids)} ({base_aid})")
        base_aid = bytearray.fromhex(base_aid)
        for j, changed_byte_value in enumerate(values_for_changed_bytes):
            print(f"Changed byte value {j + 1}/{len(values_for_changed_bytes)} ({changed_byte_value})")
            random_byte_order = byte_numbers_to_test
            random.shuffle(random_byte_order)
            for k, changed_byte_number in enumerate(random_byte_order):
                print(f"Changed byte number {k + 1}/{len(byte_numbers_to_test)} ({changed_byte_number})")
                test_single_changed_byte(result_writer, base_aid, changed_byte_number, changed_byte_value, base_major,
                                         base_minor, measurements_for_one_cap, measure_load, tidy_up, auth)
            if test_major:
                print("Major version")
                test_single_changed_byte(result_writer, base_aid, None, None, changed_byte_value, base_minor,
                                         measurements_for_one_cap, measure_load, tidy_up, auth)
            if test_minor:
                print("Minor version")
                test_single_changed_byte(result_writer, base_aid, None, None, base_major, changed_byte_value,
                                         measurements_for_one_cap, measure_load, tidy_up, auth)



def main():
    parser = argparse.ArgumentParser(
        prog="Package side channel discovery"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('-a', '--base_aid',
                        help="AID(s) in hex to use as a base for the testing",
                        required=True, nargs='+')
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--number_of_measurements', help="Number of measurements for each installation",
                        required=True, type=int)
    parser.add_argument("--measure_load", help="Whether to measure only LOAD command duration", action="store_true")
    parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+',
                        type=int)
    parser.add_argument('--changed_byte_values',
                        help="Byte values to set for the changed byte in side channel discovery mode",
                        required=True, nargs='+', type=int)
    parser.add_argument("--test_major", help="Test major version as well", action="store_true")
    parser.add_argument("--test_minor", help="Test minor version as well", action="store_true")
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro",
                        type=str)

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    package_side_channel_discovery_pc_timer(args.results_file, args.base_aid, args.byte_numbers,
                                            args.major, args.minor, args.number_of_measurements, args.measure_load,
                                            args.changed_byte_values, args.test_major, args.test_minor, args.tidy_up,
                                            args.auth)


if __name__ == '__main__':
    main()
