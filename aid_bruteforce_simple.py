import csv
import os
import subprocess
import time

from aid_side_channel_test import generate_cap_for_package_aid

VALID_CAP_FILE_PATH = "templates_ff/test_javacardx_crypto_9.cap"

def install_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name],
                          stdout=subprocess.PIPE)


def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name],
                          stdout=subprocess.PIPE)

def reset_fault_counter():
    result = install_package(VALID_CAP_FILE_PATH)

    result = result.stdout.decode("utf-8")
    if result.find("CAP loaded") == -1:
        print("CARD UNRESPONSIVE! ABORTING!")
        exit(1)

    uninstall_package(VALID_CAP_FILE_PATH)



major = 1
minor = 0

base_aid = bytearray.fromhex("A0000000620000")

result_file = open("bruteforce_results_5_6.csv", "w")
result_file_writer = csv.writer(result_file)

start_time = time.time()

for second_last_byte_value in range(256):
    for last_byte_value in range(256):
        success = False
        current_aid = base_aid.copy()
        current_aid[5] = second_last_byte_value
        current_aid[6] = last_byte_value
        print(f"Measuring: {current_aid.hex()}")
        cap_file_name = generate_cap_for_package_aid(current_aid, major, minor, second_last_byte_value, "bruteforce")
        result = install_package(cap_file_name)

        result = result.stdout.decode("utf-8")
        if result.find("CAP loaded") != -1:
            print("INSTALL SUCCESS")
            success = True
            uninstall_package(cap_file_name)

        result_file_writer.writerow([second_last_byte_value, last_byte_value, success])

        if last_byte_value % 20 == 0:
            print("Resetting fault counter...")
            print(f"Time elapsed: {(time.time() - start_time) / 3600} hours")
            reset_fault_counter()

        os.remove(cap_file_name)



