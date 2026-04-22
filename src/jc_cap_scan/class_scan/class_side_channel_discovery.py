import argparse
import csv
import os.path
import sys
from typing import Literal

from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_single_time_from_trs_file, extract_all_times_from_trs_file
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid_and_class_token
from jc_cap_scan.utils.capture_utils import capture_install_trace


def class_side_channel_discovery(results_file: str, traces_directory: str, base_aid: str, base_major: int,
                                 base_minor: int, traces_for_one_token: int, class_token_range: tuple[int, int],
                                 cp_info_type: Literal['class', 'method'], config: Config, tidy_up: bool,
                                 auth: list[str] | None = None):
    """
    Try to discovery side channel timing leakage in the installation of CAP files with different class tokens using power traces
    :param results_file: Path to results file in CSV format, where the results will be stored
    :param traces_directory: Path to directory to store the captured traces
    :param base_aid: AID to use for the CAP files
    :param base_major: Base major version to use for the CAP files
    :param base_minor: Base minor version to use for the CAP files
    :param traces_for_one_token: How many traces to capture for each class token
    :param class_token_range: Range of the class tokens to tess
    :param cp_info_type: Type of cpInfo to use to reference the class token in the generated CAP files. Either 'class' for ClassRef or 'method' for StaticMethodRef
    :param config: Config for the capture and extraction
    :param tidy_up: Whether to delete generated CAP files and captured traces after they are used
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    assert cp_info_type in ['static', 'class']
    f = open(results_file, "a")
    result_writer = csv.writer(f)
    print("Starting measurement...")

    for class_token in range(class_token_range[0], class_token_range[1]):
        print(
            f"Class token {class_token - class_token_range[0] + 1}/{class_token_range[1] - class_token_range[0]} ({class_token})")
        cp_info_number = 1 if cp_info_type == 'class' else 6
        cap_name = f"class_{base_aid}_{class_token}.cap"
        trs_file = f"class_{base_aid}_{class_token}.trs"
        generate_cap_for_package_aid_and_class_token(bytearray.fromhex(base_aid),
                                                     base_major,
                                                     base_minor,
                                                     os.path.join("templates", "generic_template"),
                                                     class_token,
                                                     cp_info_number,
                                                     cap_name)
        success, response = capture_install_trace(cap_name, traces_for_one_token, os.path.join(traces_directory, trs_file), config.capture, auth)
        times = extract_all_times_from_trs_file(os.path.join(traces_directory, trs_file), config.extraction)

        for item in times:
            result_writer.writerow([base_aid, class_token] + item)
        if tidy_up:
            os.remove(cap_name)
            os.remove(os.path.join(traces_directory, trs_file))

        print(f"Class token: {class_token}\n"
              f"Response: {response}\n"
              f"Success: {success}\n"
              f"Times: {times}")

def main():
    parser = argparse.ArgumentParser(
        prog="Class side channel discovery"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--traces_directory', help="Directory to store the captured traces", default="traces",
                                 type=str)
    parser.add_argument('--class_token_range', help="Range of class tokens to test, e.g. 0 255",
                        required=False, nargs=2, default=(0, 255), type=int)
    parser.add_argument('-a', '--base_aid', help="AID in hex to use as a base for the testing",
                        required=True, type=str)
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--cp_info_type',
                        help="cpInfo type to use for testing. class - Classref, method - Staticmethodref",
                        required=False, type=str, default='class')
    parser.add_argument('--number_of_traces', help="Number of traces to capture for each installation",
                                 required=True, type=int)
    parser.add_argument('-c', '--config',
                                 help="Configuration file", required=False,
                                 type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    config = Config.load_from_toml(args.config)
    class_side_channel_discovery(args.results_file, args.traces_directory, args.base_aid, args.major, args.minor,
                                 args.number_of_traces, args.class_token_range, args.cp_info_type, config, args.tidy_up,
                                 args.auth)


if __name__ == '__main__':
    main()