import argparse
import csv
import random
import os

from jc_cap_scan.aid_scan.aid_bruteforce import do_dummy_captures
from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.capture_utils import capture_install_trace


def test_single_changed_byte(results: dict, base_aid: bytearray, byte_number: int | None, byte_value: int | None, major: int, minor: int, num_of_traces: int, traces_directory: str, config: Config, tidy_up: bool, auth: list[str] | None = None):
    aid_modified = base_aid.copy()
    if byte_number is not None:
        aid_modified[byte_number] = byte_value

    cap_file_name = f"test_{aid_modified.hex()}_{major}_{minor}.cap"
    trs_file_name = f"test_{aid_modified.hex()}_{major}_{minor}.trs"
    generate_cap_for_package_aid(aid_modified, major, minor, os.path.join("templates", "generic_template"),
                                 cap_file_name)
    capture_install_trace(cap_file_name, num_of_traces,
                          os.path.join(traces_directory, trs_file_name),
                          config.capture, auth)
    times = extract_times_from_trs_file(
        os.path.join(traces_directory, trs_file_name), config.extraction)

    if results.get([aid_modified, major, minor]) is None:
        results[[aid_modified, major, minor]] = []
    results[[aid_modified, major, minor]].extend(times)

    if tidy_up:
        os.remove(cap_file_name)
        os.remove(os.path.join(traces_directory, trs_file_name))


def aid_side_channel_discovery(num_of_dummy_captures: int, result_file_name: str, base_aids: list[str],
                               byte_numbers_to_test: list[int],
                               base_major: int, base_minor: int, traces_for_one_cap_file: int, traces_directory: str,
                               values_for_changed_bytes: list[int], test_major: bool, test_minor: bool, config: Config, auth: list[str] | None,
                               tidy_up: bool = False):
    print("Performing dummy captures...")
    do_dummy_captures(traces_directory, num_of_dummy_captures, config.capture, auth)

    print("Starting measurement...")
    result_file = open(result_file_name, "w")
    result_file_writer = csv.writer(result_file)

    results = {}

    for i, base_aid in enumerate(base_aids):
        print(f"AID {i + 1}/{len(base_aids)} ({base_aid})")
        base_aid = bytearray.fromhex(base_aid)
        for j, changed_byte_value in enumerate(values_for_changed_bytes):
            print(f"Changed byte value {j + 1}/{len(values_for_changed_bytes)} ({changed_byte_value})")
            random_byte_order = byte_numbers_to_test
            random.shuffle(random_byte_order)
            for k, changed_byte_number in enumerate(random_byte_order):
                print(f"Changed byte number {k + 1}/{len(byte_numbers_to_test)} ({changed_byte_number})")
                test_single_changed_byte(results, base_aid, changed_byte_number, changed_byte_value, base_major, base_minor, traces_for_one_cap_file, traces_directory, config, tidy_up, auth)
            if test_major:
                print("Major version")
                test_single_changed_byte(results, base_aid, None, None, changed_byte_value, base_minor, traces_for_one_cap_file, traces_directory, config, tidy_up, auth)
            if test_minor:
                print("Minor version")
                test_single_changed_byte(results, base_aid, None, None, base_major, changed_byte_value, traces_for_one_cap_file, traces_directory, config, tidy_up, auth)

    for changed_byte_number in sorted(list(results.keys())):
        result_file_writer.writerow([changed_byte_number] + results[changed_byte_number])


def visualize_results(result_file_name: str):
    pass

def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="AID side channel discovery"
    )

    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro",
                        type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('-c', '--config', help="Configuration file", required=True, type=str)
    parser.add_argument('--number_of_dummy_captures',
                                 help="Number of traces to capture before the actual experiment starts", default=200,
                                 type=int)
    parser.add_argument('-a', '--base_aid',
                                 help="AID(s) in hex to use as a base for the testing",
                                 required=True, nargs='+')
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--number_of_traces', help="Number of traces to capture for each installation",
                                 required=True, type=int)
    parser.add_argument('--traces_directory', help="Directory to store the captured traces", default="traces",
                                 type=str)
    parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+',
                                 type=int)
    parser.add_argument('--changed_byte_values',
                                 help="Byte values to set for the changed byte in side channel discovery mode",
                                 required=True, nargs='+', type=int)
    parser.add_argument("--test_major", help="Test major version as well", action="store_true")
    parser.add_argument("--test_minor", help="Test minor version as well", action="store_true")

    args = parser.parse_args(argv)

    config = Config.load_from_toml(args.config)
    aid_side_channel_discovery(args.number_of_dummy_captures, args.results_file, args.base_aid, args.byte_numbers,
                               args.major, args.minor, args.number_of_traces, args.traces_directory,
                               args.changed_byte_values, args.test_major, args.test_minor, config, args.auth,
                               args.tidy_up)


if __name__ == '__main__':
    main(sys.argv)