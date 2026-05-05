import argparse
import csv
import os.path
import shutil
from typing import Literal

from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_diff import get_diff
from jc_cap_scan.trs_analysis.trs_window_resample import window_resample
from jc_cap_scan.utils.cap_file_utils import pack_directory_to_cap_file, uninstall
from jc_cap_scan.utils.capture_utils import capture_install_trace

COMPONENT_NAMES = [
    "Header",
    "Directory",
    "Applet",
    "Import",
    "ConstantPool",
    "Class",
    "Method",
    "StaticField",
    "RefLocation"
]

# window for window resampling
WINDOW = 2000


def change_byte_in_component(file_path: str, byte_number: int, new_value: int) -> None:
    """
    Change a single byte in a given CAP file component and save the component to the same file
    :param file_path: Path to the component
    :param byte_number: Byte number to change (0-indexed)
    :param new_value: New value for the byte
    :return:
    """
    with open(file_path, "rb") as f:
        content = f.read()
    content = bytearray(content)

    content[byte_number] = new_value

    with open(file_path, "wb") as f:
        f.write(content)


def load_scan(results_file: str, traces_directory: str, changed_byte_value: int,
              diff_algorithm: Literal['subtraction', 'periods'], diff_threshold: float, alignment_threshold: float, ignore_first_n: int, config: Config,
              tidy_up: bool,
              auth: list[str] | None = None):
    """
    Scan the full cap file and try to identify which regions of the power trace correspond to which CAP file components
    :param results_file: Path to file where to store the results
    :param traces_directory: Path to a directory where traces should be stored
    :param changed_byte_value: Value for the changed byte
    :param diff_algorithm: Algorithm to calculate diff between correct power trace and the changed one. Can be either 'periods' or 'subtraction
    :param diff_threshold: Threshold for the diff algorithm
    :param alignment_threshold: Threshold used to align the traces
    :param ignore_first_n: Do not find diff in the first n samples
    :param config: Config for the capture and extraction
    :param tidy_up: Whether to delete the generated CAP files and captured traces after they are used
    :param auth: Authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    print("Capturing base trace...")
    capture_install_trace(os.path.join("templates", "good_package.cap"), 1, os.path.join(traces_directory, "base_install.trs"), config.capture, auth)
    window_resample(WINDOW, None, False, 1, os.path.join(traces_directory, f"base_install.trs"),
                    os.path.join(traces_directory, "base_install_resampled.trs"))

    f = open(results_file, "w")
    csv_writer = csv.writer(f)

    print("Starting measurement...")
    for component in COMPONENT_NAMES:
        print(f"Testing {component} component")
        component_name = f"{component}.cap"
        component_path = os.path.join("templates", "generic_template", "test", "javacard", component_name)
        if not os.path.exists(component_path):
            print("Component does not exists in the template and will not be tested")
            continue
        component_length = os.path.getsize(component_path)
        for byte_number in range(12, component_length):
            print(f"Byte {byte_number + 1}/{component_length}")
            shutil.copytree(os.path.join("templates", "generic_template"), "tmp")
            component_path = os.path.join("tmp", "test", "javacard", component_name)
            change_byte_in_component(component_path, byte_number, changed_byte_value)
            cap_name = f"{component}_{byte_number}.cap"
            pack_directory_to_cap_file(cap_name, "tmp")
            uninstall(cap_name, auth)

            success, result = capture_install_trace(cap_name, 1,
                                                    os.path.join(traces_directory, f"{component}_{byte_number}.trs"),
                                                    config.capture, auth)

            print("Resampling...")
            window_resample(WINDOW, None, False, 1, os.path.join(traces_directory, f"{component}_{byte_number}.trs"),
                            os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"))
            print("Getting diff..")
            first_diff = get_diff(os.path.join(traces_directory, "base_install_resampled.trs"),
                                  os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"),
                                  diff_threshold, alignment_threshold,
                                  diff_algorithm, False, ignore_first_n, config.extraction)

            print(f"Component: {component}\n"
                  f"Byte number: {byte_number}\n"
                  f"Install response: {result}\n"
                  f"First diff: {first_diff}")
            csv_writer.writerow([component, byte_number, result, first_diff])

            shutil.rmtree("tmp")
            if tidy_up:
                os.remove(cap_name)

def main():
    parser = argparse.ArgumentParser(
        prog="Load scan"
    )

    parser.add_argument("--results_file", help="File to store the results", required=True, type=str)
    parser.add_argument("--traces_directory", help="Directory to store the captured traces", required=False,
                        default='traces', type=str)
    parser.add_argument("--changed_byte_value", help="Value to change the byte to", required=True, type=int)
    parser.add_argument("--diff_algorithm",
                        help="Algorithm to use for calculating the diff. Can be 'periods' or 'subtraction'",
                        required=True, type=str)
    parser.add_argument("--diff_threshold",
                        help="Threshold for the diff calculation. For 'periods' algorithm this is how much the period "
                             "should be longer or shorter to be considered different (in multiples of the base one). "
                             "For 'subtraction' algorithm this is the threshold for the difference trace.", type=float,
                        required=True)
    parser.add_argument("--alignment_threshold", help="Threshold for the alignment calculation.", type=float, required=True)
    parser.add_argument("--ignore_first_n", help="Ignore first n samples (for 'subtraction' algorithm)", type=int, required=False, default=0)
    parser.add_argument("--config", help="Path to configuration file", required=True, type=str)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()
    config = Config.load_from_toml(args.config)
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    load_scan(args.results_file, args.traces_directory, args.changed_byte_value, args.diff_algorithm,
              args.diff_threshold, args.alignment_threshold, args.ignore_first_n, config, args.tidy_up, args.auth)


if __name__ == "__main__":
    main()
