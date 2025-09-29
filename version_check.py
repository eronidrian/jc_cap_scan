import csv
import os
import subprocess

from aid_side_channel_test import generate_cap_for_package_aid

package_name = "javacard_security"
aid = bytearray.fromhex("A0000000620102")
major = 1
minor = 0

result_file = open("results.csv", "w")
csv_writer = csv.writer(result_file)

for changed_byte_value in range(256):
    print(changed_byte_value)
    success_install = False
    # generate CAP file
    generate_cap_for_package_aid(aid, major, changed_byte_value, changed_byte_value, package_name)
    # install CAP file
    result = subprocess.run(["java", "-jar", "gp.jar", "--install",
                    f"test_{package_name}_{changed_byte_value}.cap"],
                   stdout=subprocess.PIPE)
    result = result.stdout.decode("utf-8")
    if result.find("CAP loaded") != -1:
        print("Successful installation")
        success_install = True
        subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                        f"test_{package_name}_{changed_byte_value}.cap"],
                       stdout=subprocess.PIPE)

    csv_writer.writerow([changed_byte_value, success_install])
    os.remove(f"test_{package_name}_{changed_byte_value}.cap")

result_file.close()
