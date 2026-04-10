import argparse
import csv
import os
import sys
from statistics import mean

from api_specification.api_specification import API_305_SPECIFICATION
from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_times_from_trs_file
from jc_cap_scan.utils.cap_file_utils import is_installation_successful, uninstall
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.capture_utils import capture_install_trace


def aid_list_scan(results_file: str, major_range: tuple[int, int], minor_range: tuple[int, int], traces_for_one_cap: int, traces_dir: str, config: Config, tidy_up: bool, auth: list[str] | None = None):

    aid_name_map = API_305_SPECIFICATION.get_aid_name_map()
    f = open(results_file, "w")
    csv_writer = csv.writer(f)

    print("Starting measurement...")

    for aid in aid_name_map:
        # skip javacard.framework because it behaves differently then all the other packages
        if aid_name_map[aid] == "javacard.framework":
            continue
        print(f"Testing {aid_name_map[aid]}")
        for major in range(major_range[0], major_range[1]):
            print(f"Major version {major}")
            for minor in range(minor_range[0], minor_range[1]):
                print(f"Minor versin {minor}")
                cap_name = f"{aid_name_map[aid].replace(".", "_")}_{major}_{minor}.cap"
                generate_cap_for_package_aid(bytearray.fromhex(aid), major, minor, os.path.join("templates", "generic_template"), cap_name)
                supported, _ = is_installation_successful(cap_name)

                if not supported:
                    print(f"{aid_name_map[aid]} v{major}.{minor} not supported")
                    if tidy_up:
                        os.remove(cap_name)
                    break
                print(f"{aid_name_map[aid]} v{major}.{minor} is supported")
                uninstall(cap_name)

                trs_file_name = f"{aid_name_map[aid].replace(".", "_")}_{major}_{minor}.trs"
                capture_install_trace(cap_name, traces_for_one_cap, os.path.join(traces_dir, trs_file_name), config.capture, auth)
                times = extract_times_from_trs_file(os.path.join(traces_dir, trs_file_name), config.extraction)

                print(f"AID: {aid}\n"
                      f"Major: {major}\n"
                      f"Minor: {minor}\n"
                      f"Mean time: {mean(times)}\n\n")
                csv_writer.writerow([aid, major, minor] + times)
                if tidy_up:
                    os.remove(cap_name)
                    os.remove(os.path.join(traces_dir, trs_file_name))

def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="AID list scan"
    )

    parser.add_argument("--config", help="Configuration file", required=True, type=str)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro",
                        type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('--major_range', help="Range of major versions to test, e.g. 0 5",
                        required=False, nargs=2, default=(0, 3), type=int)
    parser.add_argument('--minor_range', help="Range of minor versions to test, e.g. 0 5",
                        required=False, nargs=2, default=(0, 10), type=int)
    parser.add_argument('--traces_for_one_cap', help="How many traces to capture for each CAP file", required=True,
                        type=int)
    parser.add_argument('--traces_dir', help="Directory to store the captured traces into", default="traces",
                        type=str)

    args = parser.parse_args(argv)
    config = Config.load_from_toml(args.config)
    aid_list_scan(args.results_file, args.major_range, args.minor_range, args.traces_for_one_cap, args.traces_dir,
                   args.config, args.tidy_up, args.auth)

if __name__ == '__main__':
    main(sys.argv)