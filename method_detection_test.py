import csv
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

generate_cap_for_package_aid(aid, major, minor, 0, package_name)