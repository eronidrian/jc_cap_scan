import csv
import random
import subprocess
import time
from os import path
import shutil
import os

from jcAIDScan import PackageAID

javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 0)
BASE_PATH = '.'


def format_import(packages_list):
    total_len = 1  # include count of number of packages
    for package in packages_list:
        total_len += package.get_length()

    # format of Import.cap: 04 00 len num_packages package1 package2 ... packageN
    import_section = '0400{:02x}{:02x}'.format(total_len, len(packages_list))

    # serialize all packages
    for package in packages_list:
        import_section += package.serialize()

    return import_section

def generate_cap_for_package_aid(aid, major, minor, aid_len):
    imported_packages = []
    imported_packages.append(javacard_framework)
    # imported_packages.append(java_lang)  # do not import java_lang as default (some cards will then fail to load)
    imported_packages.append(PackageAID(aid, major, minor))

    import_section = format_import(imported_packages)

    print(import_section)
    f = open(path.join(BASE_PATH, 'template', 'test', 'javacard', 'Import.cap'), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()

    # create new cap file by zip of directories
    shutil.make_archive(f'test_{aid_len}.cap', 'zip', path.join(BASE_PATH, 'template'))

    # remove zip suffix
    if os.path.exists(f'test_{aid_len}.cap'):
        os.remove(f'test_{aid_len}.cap')
    os.rename(f'test_{aid_len}.cap.zip', f'test_{aid_len}.cap')

major = 1
minor = 0
for aid_len in range(4, 15):
    aid = bytearray.fromhex("AA"*aid_len)
    generate_cap_for_package_aid(aid, major, minor, aid_len)





#############################
# PC TIMER MEASUREMENT      #
#############################
# measurements_num = 50
#
# row_names = [f"AID {i}. byte" for i in range(1, len(aid) + 1)]
# row_names.extend([
#     "Major version",
#     "Minor version",
#     "Unchanged"
# ])

# f = open(f"aid_upload_times_{package_name}.csv", "w", newline="")
# writer = csv.writer(f)
# writer.writerow(["modification"] + [i for i in range(1, 51)])
#
#
# for i in range(len(aid) + 3):
#     times = []
#     print(f"Measuring test_{package_name}_{i}.cap...")
#     times.append(row_names[i])
#     for j in range(measurements_num):
#         print(j)
#         start = time.perf_counter_ns()
#         subprocess.run(["java", "-jar", "gp.jar", "--install", f"test_{package_name}_{i}.cap"], stdout=subprocess.PIPE)
#         end = time.perf_counter_ns()
#         times.append(end - start)
#         subprocess.run(["java", "-jar", "gp.jar", "--uninstall", f"test_{package_name}_{i}.cap"], stdout=subprocess.PIPE)
#     print("Resulting times:")
#     print(times)
#     writer.writerow(times)
#
# f.close()