import csv
import os
import shutil
from os import DirEntry
from statistics import median

from measurement_script import measure_cap_file_install, measure_cap_file_call
from trs_analyser import extract_from_single_trs_file
import subprocess
from cap_parser.cap_file import CapFile

# configuration
auth = []
measurements_for_one_byte = 1
num_of_dummy_measurements = 20
index_to_extract = 2
card_name = "javacos_a_40"

def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def install_package(cap_file_name) -> str:
    message = subprocess.run(["java", "-jar", "gp.jar", "--install",
                              cap_file_name] + auth,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # uninstall_package(cap_file_name)

    message = message.stdout.decode("utf-8")
    message = message.replace('Warning: no keys given, using default test key 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace(
        '[WARN] GPSession - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)',
        '')
    message = message.replace('\n', ' ')
    message = message.strip()

    if "STRICT WARNING" in message:
        exit(1)

    return message

def is_template_correct(template_location: str) -> bool:
    cap_name = "template_test.cap"
    pack_directory_to_cap_file(cap_name, template_location)

    install_response = install_package(cap_name)
    if "CAP loaded" not in install_response:
        print(f"Template {template_location} did not install successfully")
        print(f"Response: {install_response}")
        return False

    call_response = call_package(debug=True)
    if "9000" not in call_response:
        print(f"Template {template_location} cannot be called successfully")
        print(f"Response: {call_response}")
        return False

    uninstall_package(cap_name)
    os.remove(cap_name)
    return True

def call_package(debug: bool = False) -> str:
    command_apdu = "1234000000"
    call_response_lines = subprocess.run(["java", "-jar", "gp.jar", "--apdu",
                                          "00A404000C73696D706C656170706C657400", "--apdu", command_apdu,
                                          "-d"] + auth,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    call_response_lines = call_response_lines.stdout.decode("utf-8").splitlines()

    if debug:
        for i in range(len(call_response_lines)):
            print(i, call_response_lines[i])

    command_line_num = 0
    for i, line in enumerate(call_response_lines):
        if command_apdu in line:
            command_line_num = i
            break
    response_line_num = command_line_num + 1
    call_response = call_response_lines[response_line_num].split(")")[-1].strip()

    return call_response

def pack_directory_to_cap_file(cap_name: str, directory_name: str) -> None:
    shutil.make_archive(cap_name, 'zip', os.path.join(directory_name))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)



# print("PERFORMING DUMMY MEASUREMENTS")
# for i in range(num_of_dummy_measurements):
#     print(f"{i+1}/{num_of_dummy_measurements}")
#     measure_cap_file("templates_ff/test_javacard_security_0.cap", 10, "tmp_traces")

print("STARTING MEASUREMENT")


def test(card_name: str):
    uninstall_package("good_package.cap")
    for i, entry in enumerate(sorted(os.scandir("templates"), key=lambda ent: ent.name)):
        if not entry.is_dir():
            continue

        if i != 12:
            continue

        _, _, static_or_virtual, class_name, method_name, return_or_call = entry.name.split("_")
        print(f"Testing template {entry.name}")
        if not is_template_correct(entry.path):
            print(f"Skipping template {entry.name}")
            continue
        print("Template is correct")

        # result_file = open(f"{card_name}_{entry.name}.csv", "w")
        # csv_writer = csv.writer(result_file)

        template_loaded = CapFile.load_from_directory(os.path.join(entry.path, "applets", "javacard"))
        constant_pool_entry = template_loaded.constant_pool_component.get_cp_info_by_method_name(method_name)
        #for method_token in range(256):
        for method_token in [0]:
            constant_pool_entry.info.token = method_token
            template_loaded.export_to_directory(os.path.join(f"{entry.name}_{method_token}", "applets", "javacard"))
            cap_file_name = f"{entry.name}_{method_token}.cap"
            pack_directory_to_cap_file(cap_file_name, f"{entry.name}_{method_token}")

            # measure_cap_file_install(cap_file_name, measurements_for_one_byte, "traces_install")
            measure_cap_file_call(cap_file_name, measurements_for_one_byte, "traces_call")

            #times = extract_from_single_trs_file(measurements_for_one_byte, f"traces/traces_{cap_file_name}.trs",
            #                                     index_to_extract)
            #median_time = median(times)
            # print(f"Current template: {entry.name}\n"
            #       f"Times: {times}\n"
            #       f"Median time: {median_time}\n\n")
            # csv_writer.writerow([method_token] + times)
            # os.remove(cap_file_name)
        break

if __name__ == '__main__':
    test(card_name)