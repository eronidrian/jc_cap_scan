import argparse
import sys
from argparse import ArgumentParser

from jc_cap_scan.aid_scan.aid_bruteforce import aid_bruteforce
from jc_cap_scan.aid_scan.aid_side_channel_discovery import aid_side_channel_discovery
from jc_cap_scan.class_scan.class_bruteforce import class_bruteforce
from jc_cap_scan.config.config import Config, MeasurementConfig, ExtractionConfig
from jc_cap_scan.method_scan.method_bruteforce import method_bruteforce
from jc_cap_scan.setup.measurement_setup import capture_sample_install_trace, capture_sample_call_trace
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file


def init_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jcCAPscan",
        description="Tool for assessment and exploitation of side channel leakage during installation of CAP file on a Javacard",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--auth', help="Authentication to use for the connection to the card. Enter as arguments to the GPPro", type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",action='store_true', default=False)
    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)


    subparsers = parser.add_subparsers(dest='module',
                                       help='The module you want to use. One of "aid_scan", "class_scan", "method_scan" and "setup"',
                                       required=True)

    aid_scan_parser = subparsers.add_parser('aid_scan')
    mode = aid_scan_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bruteforce', help="Use bruteforce mode", action='store_true')
    mode.add_argument('--side_channel_discovery', help="Use side channel discovery mode", action='store_true')
    aid_scan_parser.add_argument('-c', '--config', help="Configuration file", required=True, type=str)
    aid_scan_parser.add_argument('--number_of_dummy_measurements', help="Number of traces to capture before the actual experiment starts", default=200, type=int)
    aid_scan_parser.add_argument('-a', '--base_aid', help="AID(s) in hex to use as a base for the testing. Bruteforce does not support multiple AIDs", required=True, nargs='+')
    aid_scan_parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    aid_scan_parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    aid_scan_parser.add_argument('--number_of_measurements', help="Number of measurements to perform for each CAP file", required=True, type=int)
    aid_scan_parser.add_argument('--traces_directory', help="Directory to store the captured traces", default="traces", type=str)
    aid_scan_parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+', type=int)
    aid_scan_parser.add_argument('--changed_byte_values', help="Byte values to set for the changed byte in side channel discovery mode", required='--bruteforce' in sys.argv[1], nargs='+', type=int)

    class_scan_parser = subparsers.add_parser('class_scan')
    mode = class_scan_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bruteforce', help="Use bruteforce mode", action='store_true')
    class_scan_parser.add_argument('--class_token_range', help="Range of class tokens to test, e.g. 0 255", required=False, nargs=2, default=(0, 255), type=int)
    class_scan_parser.add_argument('-a', '--base_aid', help="AID(s) in hex to use as a base for the testing. Bruteforce does not support multiple AIDs", required=True, nargs='+')
    class_scan_parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    class_scan_parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    class_scan_parser.add_argument('--cp_info_type', help="cpInfo type to use for testing. 1 - Classref, 6 - Staticmethodref", required=False, type=int, default=1)

    method_scan_parser = subparsers.add_parser('method_scan')
    mode = method_scan_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bruteforce', help="Use bruteforce mode", action='store_true')
    method_scan_parser.add_argument('--template_number', help="Template CAP file number to use", required=False, type=int)
    method_scan_parser.add_argument('--method_token_range', help="Range of method tokens to test, e.g. 0 255", required=False, nargs=2, default=(0, 255), type=int)

    setup_measurement_parser = subparsers.add_parser('setup_measurement')
    call_or_install = setup_measurement_parser.add_mutually_exclusive_group(required=True)
    call_or_install.add_argument('--install', help="Capture install trace", action='store_true')
    call_or_install.add_argument('--call', help="Capture call trace", action='store_true')
    setup_measurement_parser.add_argument('--cap_file', help="Path to CAP file to use for the measurement.", required=True, type=str)
    setup_measurement_parser.add_argument('--show', help="Whether to show the captured trace after measurement", action='store_true', default=False)
    setup_measurement_parser.add_argument('--config', help="Measurement configuration file in toml format. If not provided, default values will be used", required=False, type=str)
    extraction_measurement_parser = subparsers.add_parser('setup_extraction')
    mode.add_argument('--extraction', help="Use trace extraction mode", action='store_true')
    extraction_measurement_parser.add_argument('--trs_file', help="Path to the .trs file to extract the times from", required=True, type=str)
    extraction_measurement_parser.add_argument('--number_of_measurements', help="Number of measurements in the .trs file", required=True, type=int)
    extraction_measurement_parser.add_argument('--number_of_samples', help="Number of samples for each measurement in the .trs file", required=True, type=int)
    extraction_measurement_parser.add_argument('--config', help="Extraction configuration file in toml format", required=True, type=str)

    return parser

def main():

    parser = init_parser()
    args = parser.parse_args()

    if args.module == 'aid_scan':
        config = Config.load_from_toml(args.config)
        if args.bruteforce:
            aid_bruteforce(args.number_of_dummy_measurements, args.results_file, args.base_aid[0], args.byte_numbers, args.major, args.minor, args.number_of_measurements, args.traces_directory, config, args.auth, args.tidy_up)
        if args.side_channel_discovery:
            aid_side_channel_discovery(args.number_of_dummy_measurements, args.results_file, args.base_aid, args.byte_numbers, args.major, args.minor, args.number_of_measurements, args.traces_directory, args.changed_byte_values, config, args.auth, args.tidy_up)
    if args.module == 'class_scan':
        if args.bruteforce:
            class_bruteforce(args.results_file, args.class_token_range, args.base_aid[0], args.major, args.minor, args.cp_info_type, args.tidy_up, args.auth)
    if args.module == 'method_scan':
        if args.bruteforce:
            method_bruteforce(args.results_file, args.tidy_up, args.template_number, args.method_token_range, args.auth)
    if args.module == 'setup_measurement':
        config = MeasurementConfig.load_from_toml(args.config) if args.config else None
        if args.install:
            capture_sample_install_trace(args.results_file, args.cap_file, config, args.show, args.auth)
        if args.call:
            capture_sample_call_trace(args.results_file, args.cap_file, config, args.show, args.auth)
    if args.module == 'setup_extraction':
        config = ExtractionConfig.load_from_toml(args.config)
        extract_times_from_trs_file(args.trs_file, config)

if __name__ == '__main__':
    main()
