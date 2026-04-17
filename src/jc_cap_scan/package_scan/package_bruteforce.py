import argparse
import csv
import os
import sys
from typing import Literal
import matplotlib as mpl


import pandas as pd
from matplotlib import pyplot as plt

from jc_cap_scan.config.config import CaptureConfig, Config
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.capture_utils import capture_install_trace, get_actual_sample_interval
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file


def do_dummy_captures(traces_directory: str, num_of_repetitions: int, capture_config: CaptureConfig,
                      auth: list[str] | None = None) -> None:
    """
    Capture traces and immediately remove them. Used to 'warm up' the setup before the actual experiment.
    :param traces_directory: Directory to store the traces into
    :param num_of_repetitions: Number of dummy traces to capture
    :param capture_config: Config for the capture
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :return: 
    """
    if num_of_repetitions == 0:
        return

    base_aid = bytearray.fromhex("ff" * 7)
    base_major, base_minor = (1, 0)
    cap_name = f"{base_aid.hex()}.cap"
    trs_file_name = "dummy.trs"
    generate_cap_for_package_aid(base_aid, base_major, base_minor,
                                                 os.path.join("templates", "generic_template"),
                                                 cap_name)
    for i in range(num_of_repetitions):
        print(f"Dummy capture {i + 1}/{num_of_repetitions}")
        capture_install_trace(cap_name, 1, os.path.join(traces_directory, trs_file_name), capture_config, auth)
    os.remove(cap_name)
    os.remove(os.path.join(traces_directory, trs_file_name))


def package_bruteforce(results_file: str, traces_directory: str, base_aid: str, byte_numbers: list[int],
                       base_major: int, base_minor: int, traces_for_one_byte: int, num_of_dummy_captures: int,
                       config: Config, tidy_up: bool, auth: list[str] | None = None) -> None:
    """
    Brute-force attack on the AID of a package using timing side-channels. For each byte specified in byte_numbers, it tries all 256 possible values and captures traces for each of them. The durations extracted from the traces are stored in a CSV file.
    :param num_of_dummy_captures: Number of dummy captures to perform before the actual experiment to 'warm up' the setup
    :param results_file: File to stare the results into (CSV format)
    :param base_aid: AID to use as a base for the bruteforce")
    :param byte_numbers: Byte numbers to brute-force (0-indexed, relative to the start of the AID)
    :param base_major: Major version of the package with base_aid
    :param base_minor: Minor version of the package with base_aid
    :param traces_for_one_byte: How many traces to capture for each byte value
    :param traces_directory: Directory to store the captured traces into
    :param config: Config for the capture and extraction
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :param tidy_up: Remove the generated CAP files and traces after the experiment is done
    :return:
    """
    print("Performing dummy captures...")
    do_dummy_captures(traces_directory, num_of_dummy_captures, config.capture, auth)

    print("Starting measurement...")
    f = open(results_file, "w")
    result_writer = csv.writer(f)

    for i, byte_number in enumerate(byte_numbers):
        print(f"Byte {i + 1}/{len(byte_numbers)} ({byte_number})")
        for byte_value in range(256):
            current_aid = bytearray.fromhex(base_aid)
            current_aid[byte_number] = byte_value
            print(f"AID {byte_value + 1}/256 ({current_aid.hex()}")

            cap_name = f"{current_aid.hex()}.cap"
            trs_file_name = f"{current_aid.hex()}.trs"
            generate_cap_for_package_aid(current_aid, base_major, base_minor,
                                                         'templates/template_generic',
                                                         cap_name)
            print("Capturing traces...")
            capture_install_trace(cap_name, traces_for_one_byte,
                                  os.path.join(traces_directory, trs_file_name),
                                  config.capture, auth)
            print("Extracting times...")
            times = extract_times_from_trs_file(os.path.join(traces_directory, trs_file_name),
                                                config.extraction)
            result_writer.writerow([byte_number, byte_value] + times)
            if tidy_up:
                os.remove(cap_name)
                os.path.join(traces_directory, trs_file_name)

            print(f"AID: {current_aid.hex()}\n"
                  f"Times: {times}")





    # return ax
    # plt.show()



def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="Package bruteforce"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--traces_directory', help="Directory to store the captured traces", default="traces",
                                 type=str)
    parser.add_argument('--number_of_dummy_captures',
                                 help="Number of traces to capture before the actual experiment starts", default=200,
                                 type=int)
    parser.add_argument('-a', '--base_aid',
                                 help="AID(s) in hex to use as a base for the testing",
                                 required=True, type=str)
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--number_of_traces', help="Number of traces to capture for each installation",
                                 required=True, type=int)
    parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+',
                                 type=int)
    parser.add_argument('-c', '--config', help="Configuration file", required=True, type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args(argv)

    config = Config.load_from_toml(args.config)
    package_bruteforce(args.results_file, args.traces_directory, args.base_aid, args.byte_numbers, args.major,
                       args.minor, args.number_of_traces, args.number_of_dummy_captures, config, args.tidy_up,
                       args.auth)


if __name__ == '__main__':
    config = Config.load_from_toml("config/javacos_a_40_config.toml")
    result_files = [f"~/Downloads/diplomka/aid_results/javacos_a_40/bruteforce_attempt_2/bruteforce_results_{aid}.csv" for aid in ["xxFFFFFFFFFFFF", "A0xxFFFFFFFFFF", "A000xxFFFFFFFF", "A00000xxFFFFFF", "A0000000xxFFFF"]]
    visualize_results(result_files,config.capture, [0, 160, 98], 'save', 'javacos_a_40_experiment_3.pgf')
    # main(sys.argv[1:])
