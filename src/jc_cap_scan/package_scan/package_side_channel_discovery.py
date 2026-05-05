import argparse
import csv
import random
import os
from _csv import Writer


from jc_cap_scan.package_scan.package_bruteforce import do_dummy_captures
from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_single_time_from_trs_file, extract_all_times_from_trs_file
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.capture_utils import capture_install_trace


def test_single_changed_byte(results_writer: Writer, base_aid: bytearray, byte_number: int | None, byte_value: int | None,
                             major: int, minor: int, num_of_traces: int, traces_directory: str, config: Config,
                             tidy_up: bool, auth: list[str] | None = None):
    """
    Capture power trace and extract time for single CAP file
    :param results_writer: CSV writer for writing results
    :param base_aid: AID to include in the Import component of the CAP file
    :param byte_number: Byte number in the AID to change (0-indexed). If None, no byte will be changed
    :param byte_value: Value to use to change the AID byte
    :param major: Major version of the package
    :param minor: Minor version of the package
    :param num_of_traces: Number of traces to capture of the CAP file installation
    :param traces_directory: Path to a directory where to store the traces
    :param config: Config to use for the capture and extraction
    :param tidy_up: Whether to delete the generated CAP file and captured traces after they are used
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    aid_modified = base_aid.copy()
    if byte_number is not None and byte_value is not None:
        aid_modified[byte_number] = byte_value

    cap_name = f"test_{aid_modified.hex()}_{major}_{minor}.cap"
    trs_file_name = f"test_{aid_modified.hex()}_{major}_{minor}.trs"
    generate_cap_for_package_aid(aid_modified, major, minor, os.path.join("templates", "generic_template"),
                                 cap_name)
    _, message = capture_install_trace(cap_name, num_of_traces,
                          os.path.join(traces_directory, trs_file_name),
                          config.capture, auth)
    times = extract_all_times_from_trs_file(
        os.path.join(traces_directory, trs_file_name), config.extraction)

    for item in times:
        results_writer.writerow([base_aid.hex(), byte_number, major, minor] + item)

    if tidy_up:
        os.remove(cap_name)
        os.remove(os.path.join(traces_directory, trs_file_name))


def package_side_channel_discovery(results_file: str, traces_directory: str, base_aids: list[str],
                                   byte_numbers_to_test: list[int], base_major: int, base_minor: int,
                                   traces_for_one_cap: int, num_of_dummy_captures: int,
                                   values_for_changed_bytes: list[int], test_major: bool, test_minor: bool,
                                   config: Config, tidy_up: bool, auth: list[str] | None = None):
    """
    Discover whether package finding algorithm on the card has side-channel timing leakage
    :param results_file: Path to file to store the results in CSV format
    :param traces_directory: Path to a directory where to store the traces
    :param base_aids: AIDs to include in the Import component one by one of the CAP file, in hex format
    :param byte_numbers_to_test: Byte numbers in the AID to change (0-indexed). For each byte number, all values specified in values_for_changed_bytes will be tested
    :param base_major: Base major version to use
    :param base_minor: Base minor version to use
    :param traces_for_one_cap: Number of traces to capture for each CAP file
    :param num_of_dummy_captures: Number of captures to do before the actual measurement to 'warm up' the setup
    :param values_for_changed_bytes: Values to use for the changed byte. Each value will be sequentially used
    :param test_major: Whether to test the major version as well
    :param test_minor: Whether to test the minor version as well
    :param config: Config to use for the capture and extraction
    :param tidy_up: Whether to delete the generated CAP files and captured traces after they are used
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :return:
    """

    print("Performing dummy captures...")
    do_dummy_captures(traces_directory, num_of_dummy_captures, config.capture, auth)

    print("Starting measurement...")
    f = open(results_file, "a")
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
                                         base_minor, traces_for_one_cap, traces_directory, config, tidy_up, auth)
            if test_major:
                print("Major version")
                test_single_changed_byte(result_writer, base_aid, None, None, changed_byte_value, base_minor,
                                         traces_for_one_cap, traces_directory, config, tidy_up, auth)
            if test_minor:
                print("Minor version")
                test_single_changed_byte(result_writer, base_aid, None, None, base_major, changed_byte_value,
                                         traces_for_one_cap, traces_directory, config, tidy_up, auth)


def main():
    parser = argparse.ArgumentParser(
        prog="Package side channel discovery"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--traces_directory', help="Directory to store the captured traces", default="traces",
                        type=str)
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
    parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+',
                        type=int)
    parser.add_argument('--changed_byte_values',
                        help="Byte values to set for the changed byte in side channel discovery mode",
                        required=True, nargs='+', type=int)
    parser.add_argument("--test_major", help="Test major version as well", action="store_true")
    parser.add_argument("--test_minor", help="Test minor version as well", action="store_true")
    parser.add_argument('-c', '--config', help="Configuration file", required=True, type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    config = Config.load_from_toml(args.config)
    package_side_channel_discovery(args.results_file, args.traces_directory, args.base_aid, args.byte_numbers,
                                   args.major, args.minor, args.number_of_traces, args.number_of_dummy_captures,
                                   args.changed_byte_values, args.test_major, args.test_minor, config, args.tidy_up,
                                   args.auth)


if __name__ == '__main__':
    main()
