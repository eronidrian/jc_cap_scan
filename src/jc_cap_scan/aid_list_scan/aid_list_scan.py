import argparse
import csv
import os

from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_single_time_from_trs_file
from jc_cap_scan.utils.cap_file_utils import is_installation_successful, uninstall
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid
from jc_cap_scan.utils.capture_utils import capture_install_trace

# JC API packages with few additional packages
aid_name_map = {
    "A0000000620001": "java.lang",
    "A0000000620002": "java.io",
    "A0000000620003": "java.rmi",
    "A0000000620101" : "javacard.framework",
    "A0000000620102" : "javacard.security",
    "A0000000620201": "javacardx.crypto",
    "A0000000620202": "javacardx.biometry",
    "A0000000620203": "javacardx.external",
    "A0000000620204": "javacardx.biometry1toN",
    "A0000000620205": "javacardx.security",
    "A000000062020501": "javacardx.security.cert",
    "A000000062020502" : "javacardx.security.derivation",
    "A000000062020503": "javacardx.security.util",
    "A000000062020801": "javacardx.framework.util",
    "A00000006202080101": "javacardx.framework.util.intx",
    "A000000062020802": "javacardx.framework.math",
    "A000000062020803": "javacardx.framework.tlv",
    "A000000062020804": "javacardx.framework.string",
    "A000000062020805": "javacardx.framework.event",
    "A000000062020806": "javacardx.framework.nio",
    "A000000062020807" : "javacardx.framework.time",
    "A0000000620209": "javacardx.apdu",
    "A000000062020901": "javacardx.apdu.util",
    "A00000015100": "org.globalplatform",
    "A00000015102": "org.globalplatform.contactless",
    "A00000015103": "org.globalplatform.securechannel",
    "A00000015104": "org.globalplatform.securechannel.provider",
    "A00000015105": "org.globalplatform.privacy",
    "A00000015106": "org.globalplatform.filesystem",
    "A00000015107": "org.globalplatform.upgrade",
    "A0000000030000": "visa.openplatform"
}


def aid_list_scan(results_file: str, traces_directory: str, traces_for_one_cap: int, major_range: tuple[int, int],
                  minor_range: tuple[int, int], config: Config, tidy_up: bool, auth: list[str] | None = None):
    """
    Measure valid installation of different packages and try to see differences in the installation times
    :param results_file: File to store the results in CSV format
    :param traces_directory: Directory to store the captured traces into, has to exist
    :param traces_for_one_cap: How many traces to capture for each CAP file
    :param major_range: Range of package major version to test
    :param minor_range: Range of package minor version to test
    :param config: Configuration for the testing
    :param tidy_up: Whether to remove captured traces and generated CAP files after they are used
    :param auth: Authentication for the card, if needed to install CAP files
    :return:
    """

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

                # first, check whether the package is supported by the card, if not, do not test it
                supported, _ = is_installation_successful(cap_name, auth)
                if not supported:
                    print(f"{aid_name_map[aid]} v{major}.{minor} not supported")
                    if tidy_up:
                        os.remove(cap_name)
                    break
                print(f"{aid_name_map[aid]} v{major}.{minor} is supported")
                uninstall(cap_name, auth)

                trs_file_name = f"{aid_name_map[aid].replace(".", "_")}_{major}_{minor}.trs"
                capture_install_trace(cap_name, traces_for_one_cap, os.path.join(traces_directory, trs_file_name), config.capture, auth)
                times = extract_single_time_from_trs_file(os.path.join(traces_directory, trs_file_name), config.extraction)

                print(f"AID: {aid}\n"
                      f"Major: {major}\n"
                      f"Minor: {minor}\n"
                      f"Times: {times}\n\n")
                csv_writer.writerow([aid, major, minor] + times)
                if tidy_up:
                    os.remove(cap_name)
                    os.remove(os.path.join(traces_directory, trs_file_name))




def main():
    parser = argparse.ArgumentParser(
        prog="AID list scan",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-r', '--results_file', help="File to store the results into", required=True, type=str)
    parser.add_argument('--traces_dir', help="Directory to store the captured traces into", default="traces",
                        type=str)
    parser.add_argument('--traces_for_one_cap', help="How many traces to capture for each CAP file", required=True,
                        type=int)
    parser.add_argument('--major_range', help="Range of major versions to test, e.g. 0 5",
                        required=False, nargs=2, default=(0, 3), type=int)
    parser.add_argument('--minor_range', help="Range of minor versions to test, e.g. 0 5",
                        required=False, nargs=2, default=(0, 10), type=int)
    parser.add_argument("--config", help="Path to configuration file", required=True, type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    config = Config.load_from_toml(args.config)
    aid_list_scan(args.results_file, args.traces_dir, args.traces_for_one_cap, args.major_range, args.minor_range,
                  config, args.tidy_up, args.auth)

if __name__ == '__main__':
    main()