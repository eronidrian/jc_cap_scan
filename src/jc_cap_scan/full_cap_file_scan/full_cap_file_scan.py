# capture base power trace
# change a single byte in the cap file (to 0xff)
# capture power trace and result of the installation (patch gppro)
    # repeat with a different changed byte value if the installation was successful?
# window resample the power trace
# select region where the power trace starts to deviate from the base (new script)
import csv
import os.path
import shutil

from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_diff import get_first_difference
from jc_cap_scan.trs_analysis.trs_window_resample import window_resample
from jc_cap_scan.utils.cap_file_utils import pack_directory_to_cap_file, uninstall
from jc_cap_scan.utils.measurement_utils import measure_cap_file_install

def change_byte_in_component(file_path: str, byte_number: int, new_value: int) -> None:
    with open(file_path, "rb") as f:
        content = f.read()
    content = bytearray(content)

    content[byte_number] = new_value

    with open(file_path, "wb") as f:
        f.write(content)

component_names = [
    "Import",
    "ConstantPool",
    "Class",
    "Method",
    "StaticField",
    "ReferenceLocation",
    "Export",
    "Descriptor",
]

def main(config: Config, auth: list[str] | None, changed_byte_value: int, traces_directory: str, results_file: str, tidy_up: bool):
    # measure_cap_file_install(os.path.join("templates", "good_package.cap"), 1, os.path.join(traces_directory, "base_install.trs"), config.measurement, auth)
    # window_resample(1000, None, False, 1, os.path.join(traces_directory, f"base_install.trs"),
    #                 os.path.join(traces_directory, "base_install_resampled.trs"))

    f = open(results_file, "a")
    csv_writer = csv.writer(f)

    for component in component_names:
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
            success, result = measure_cap_file_install(cap_name, 1, os.path.join(traces_directory, f"{component}_{byte_number}.trs"), config.measurement, auth)
            if result == f"{cap_name} loaded: test 73696D706C65":
                result = "CAP loaded"
            print("Resampling...")
            window_resample(1000, None, False, 1, os.path.join(traces_directory, f"{component}_{byte_number}.trs"), os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"))
            print("Getting diff..")
            first_diff = get_first_difference(os.path.join(traces_directory, "base_install_resampled.trs"), os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs"), 15)
            print(f"Component: {component}\n"
                  f"Byte number: {byte_number}\n"
                  f"Install response: {result}\n"
                  f"First diff: {first_diff}")
            csv_writer.writerow([component, byte_number, result, first_diff])
            uninstall(cap_name)

            shutil.rmtree("tmp")
            if tidy_up:
                os.remove(cap_name)
        exit()








if __name__ == '__main__':
    config = Config.load_from_toml("config/javacos_a_40_config.toml")
    main(config, None, 0xff, "traces", "results.csv", True)