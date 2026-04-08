import argparse
import csv
import os.path
import shutil
import sys
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
    "RefLocation",
]

WINDOW = 2000
THRESHOLD = 0.5

def change_byte_in_component(file_path: str, byte_number: int, new_value: int) -> None:
    with open(file_path, "rb") as f:
        content = f.read()
    content = bytearray(content)

    content[byte_number] = new_value

    with open(file_path, "wb") as f:
        f.write(content)


def full_cap_file_scan(config: Config, changed_byte_value: int, traces_directory: str, results_file: str, diff_algorithm: Literal['subtraction', 'periods'], tidy_up: bool, auth: list[str] | None = None):
    print("Capturing base trace...")
    capture_install_trace(os.path.join("templates", "good_package.cap"), 1, os.path.join(traces_directory, "base_install.trs"), config.capture, auth)
    window_resample(WINDOW, None, False, 1, os.path.join(traces_directory, f"base_install.trs"),
                    os.path.join(traces_directory, "base_install_resampled.trs"))

    f = open(results_file, "a")
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
        for byte_number in range(component_length):
            print(f"Byte {byte_number + 1}/{component_length}")
            shutil.copytree(os.path.join("templates", "generic_template"), "tmp")
            component_path = os.path.join("tmp", "test", "javacard", component_name)
            change_byte_in_component(component_path, byte_number, changed_byte_value)
            cap_name = f"{component}_{byte_number}.cap"
            pack_directory_to_cap_file(cap_name, "tmp")
            uninstall(cap_name)
            success, result = capture_install_trace(cap_name, 1, os.path.join(traces_directory, f"{component}_{byte_number}.trs"), config.capture, auth)

            if result == f"{cap_name} loaded: test 73696D706C65":
                result = "CAP loaded"

            print("Resampling...")
            window_resample(WINDOW, None, False, 1, os.path.join(traces_directory, f"{component}_{byte_number}.trs"), os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"))
            print("Getting diff..")
            first_diff = get_diff(os.path.join(traces_directory, "base_install_resampled.trs"), os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"), THRESHOLD, diff_algorithm, config.extraction)
            print(f"Component: {component}\n"
                  f"Byte number: {byte_number}\n"
                  f"Install response: {result}\n"
                  f"First diff: {first_diff}")
            csv_writer.writerow([component, byte_number, result, first_diff])
            uninstall(cap_name)

            shutil.rmtree("tmp")
            if tidy_up:
                os.remove(cap_name)

def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="Full CAP file scan"
    )

    parser.add_argument("--config", help="Configuration file", required=True, type=str)
    parser.add_argument("--changed_byte_value", help="Value to change the byte to", required=True, type=int)
    parser.add_argument("--traces_directory", help="Directory to store the captured traces", required=False, default='traces', type=str)
    parser.add_argument("--results_file", help="File to store the results", required=True, type=str)
    parser.add_argument("--diff_algorithm", help="Algorithm to use for calculating the diff. Can be 'periods' or 'subtraction'", required=True, type=str,)
    parser.add_argument('--tidy_up', help="Whether to delete the captured traces and created CAP files",
                        action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro",
                        type=str)

    args = parser.parse_args(argv)
    config = Config.load_from_toml(args.config)
    full_cap_file_scan(config, args.changed_byte_value, args.traces_directory, args.results_file, args.diff_algorithm, args.tidy_up, args.auth)

if __name__ == "__main__":
    main(sys.argv)