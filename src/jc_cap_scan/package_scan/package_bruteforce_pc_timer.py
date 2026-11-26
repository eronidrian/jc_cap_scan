import argparse
import csv
import os

from jc_cap_scan.package_scan.package_side_channel_discovery_pc_timer import measure_time_load, measure_time_full
from jc_cap_scan.utils.cap_manipulation_utils import generate_cap_for_package_aid



def package_bruteforce(results_file: str, base_aid: str, byte_numbers: list[int],
                       base_major: int, base_minor: int, num_of_measurements: int, measure_load: bool, tidy_up: bool, auth: list[str] | None = None) -> None:
    """
    Brute-force attack on the AID of a package using timing side-channels. For each byte specified in byte_numbers, it tries all 256 possible values and captures traces for each of them. The durations extracted from the traces are stored in a CSV file.
    :param results_file: File to stare the results into (CSV format)
    :param base_aid: AID to use as a base for the bruteforce")
    :param byte_numbers: Byte numbers to brute-force (0-indexed, relative to the start of the AID)
    :param base_major: Major version of the package with base_aid
    :param base_minor: Minor version of the package with base_aid
    :param num_of_measurements: Number of measurements for one CAP file
    :param measure_load: Whether to measure the LOAD command (alternative is to measure the whole installation)
    :param auth: GP authentication, if it's needed to install CAP files onto the card
    :param tidy_up: Remove the generated CAP files and traces after the experiment is done
    :return:
    """

    print("Starting measurement...")
    f = open(results_file, "w")
    result_writer = csv.writer(f)

    for i, byte_number in enumerate(byte_numbers):
        print(f"Byte {i + 1}/{len(byte_numbers)} ({byte_number})")
        for byte_value in range(256):
            current_aid = bytearray.fromhex(base_aid)
            current_aid[byte_number] = byte_value
            print(f"AID {byte_value + 1}/256 ({current_aid.hex()})")

            cap_name = f"{current_aid.hex()}.cap"
            generate_cap_for_package_aid(current_aid, base_major, base_minor,
                                                         'templates/generic_template',
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

            result_writer.writerow([byte_number, byte_value] + times)

            if tidy_up:
                os.remove(cap_name)

            print(f"AID: {current_aid.hex()}\n"
                  f"Times: {times}")





def main():
    parser = argparse.ArgumentParser(
        prog="Package bruteforce"
    )

    parser.add_argument('-r', '--results_file', help="File to store the results", required=True, type=str)
    parser.add_argument('-a', '--base_aid',
                                 help="AID(s) in hex to use as a base for the testing",
                                 required=True, type=str)
    parser.add_argument('--major', help="Major version to use for the base package", default=1, type=int)
    parser.add_argument('--minor', help="Minor version to use for the base package", default=0, type=int)
    parser.add_argument('--number_of_measurements', help="Number of measurements for each CAP file",
                                 required=True, type=int)
    parser.add_argument('-n', '--byte_numbers', help="Byte numbers to test", required=True, nargs='+',
                                 type=int)
    parser.add_argument('-l', '--measure_load', help="Whether to measure the LOAD command processing",
                                 action='store_true')
    parser.add_argument('--tidy_up', help="Whether to delete created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"

    package_bruteforce(args.results_file, args.base_aid, args.byte_numbers, args.major,
                       args.minor, args.number_of_measurements, args.measure_load , args.tidy_up,
                       args.auth)


if __name__ == '__main__':
    main()
