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

def generate_cap_for_package_aid(aid, major, minor, version, package_name):
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
    shutil.make_archive(f'test_{package_name}_{version}.cap', 'zip', path.join(BASE_PATH, 'template'))

    # remove zip suffix
    if os.path.exists(f'test_{package_name}_{version}.cap'):
        os.remove(f'test_{package_name}_{version}.cap')
    os.rename(f'test_{package_name}_{version}.cap.zip', f'test_{package_name}_{version}.cap')


package_name = "javacard_security"
aid = bytearray.fromhex("A0000000620102")
major = 1
minor = 0

modified_byte_value = 0xee

for i in range(len(aid)):
    aid_modified = aid.copy()
    aid_modified[i] = modified_byte_value
    generate_cap_for_package_aid(aid_modified, major, minor, i, package_name)

generate_cap_for_package_aid(aid, modified_byte_value, minor, len(aid), package_name)
generate_cap_for_package_aid(aid, major, modified_byte_value, len(aid) + 1, package_name)

generate_cap_for_package_aid(aid, major, minor, len(aid) + 2, package_name)

measurements_num = 50

row_names = [f"AID {i}. byte" for i in range(1, len(aid) + 1)]
row_names.extend([
    "Major version",
    "Minor version",
    "Unchanged"
])

f = open(f"aid_upload_times_{package_name}.csv", "w", newline="")
writer = csv.writer(f)
writer.writerow(["modification"] + [i for i in range(1, 51)])


for i in range(len(aid) + 3):
    times = []
    print(f"Measuring test_{package_name}_{i}.cap...")
    times.append(row_names[i])
    for j in range(measurements_num):
        print(j)
        start = time.perf_counter_ns()
        subprocess.run(["java", "-jar", "gp.jar", "--install", f"test_{package_name}_{i}.cap"], stdout=subprocess.PIPE)
        end = time.perf_counter_ns()
        times.append(end - start)
        subprocess.run(["java", "-jar", "gp.jar", "--uninstall", f"test_{package_name}_{i}.cap"], stdout=subprocess.PIPE)
    print("Resulting times:")
    print(times)
    writer.writerow(times)

f.close()