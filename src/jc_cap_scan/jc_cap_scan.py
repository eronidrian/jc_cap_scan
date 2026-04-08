import argparse
import sys
from argparse import ArgumentParser

from jc_cap_scan.aid_scan import aid_bruteforce
from jc_cap_scan.aid_scan import aid_side_channel_discovery
from jc_cap_scan.class_scan import class_bruteforce
from jc_cap_scan.class_scan import class_side_channel_discovery
from jc_cap_scan.config.config import Config, CaptureConfig, ExtractionConfig
from jc_cap_scan.field_scan import field_bruteforce
from jc_cap_scan.full_cap_file_scan import full_cap_file_scan
from jc_cap_scan.method_scan import method_bruteforce
from jc_cap_scan.setup import capture_setup
from jc_cap_scan.setup import extraction_setup
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file


def init_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jcCAPscan",
        description="Tool for assessment and exploitation of side channel leakage during installation of CAP file on a Javacard",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    module = parser.add_mutually_exclusive_group(required=True)
    module.add_argument('--aid_bruteforce', action='store_true')
    module.add_argument('--aid_side_channel_discovery', action='store_true')
    module.add_argument('--class_bruteforce', action='store_true')
    module.add_argument('--class_side_channel_discovery', action='store_true')
    module.add_argument('--field_bruteforce', action='store_true')
    module.add_argument('--method_bruteforce', action='store_true')
    module.add_argument('--capture_setup', action='store_true')
    module.add_argument('--extraction_setup', action='store_true')
    module.add_argument('--full_cap_file_scan', action='store_true')

    return parser

def main():

    parser = init_parser()
    args, args_to_be_passed = parser.parse_known_args()

    if args.aid_bruteforce:
        aid_bruteforce.main(args_to_be_passed)
    if args.aid_side_channel_discovery:
        aid_side_channel_discovery.main(args_to_be_passed)
    if args.class_bruteforce:
        class_bruteforce.main(args_to_be_passed)
    if args.class_side_channel_discovery:
        class_side_channel_discovery.main(args_to_be_passed)
    if args.field_bruteforce:
        field_bruteforce.main(args_to_be_passed)
    if args.method_bruteforce:
        method_bruteforce.main(args_to_be_passed)
    if args.capture_setup:
        capture_setup.main(args_to_be_passed)
    if args.extraction_setup:
        extraction_setup.main(args_to_be_passed)
    if args.full_cap_file_scan:
        full_cap_file_scan.main(args_to_be_passed)


if __name__ == '__main__':
    main()
