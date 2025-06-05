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


def modify_package_aid(aid: bytearray, major: int, minor: int) -> None:
    imported_packages = []
    imported_packages.append(javacard_framework)
    # imported_packages.append(java_lang)  # do not import java_lang as default (some cards will then fail to load)
    imported_packages.append(PackageAID(aid, major, minor))

    import_section = format_import(imported_packages)

    f = open(path.join(BASE_PATH, 'template_class', 'test', 'javacard', 'Import.cap'), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()


def modify_class_token(class_token: int) -> None:
    f = open(path.join(BASE_PATH, 'template_class', 'test', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[41] = 1
    hex_array[43] = int(class_token)
    f = open(path.join(BASE_PATH, 'template_class', 'test', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()


def modify_method_token(method_token: int) -> None:
    f = open(path.join(BASE_PATH, 'template_class', 'test', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[44] = int(method_token)
    f = open(path.join(BASE_PATH, 'template_class', 'test', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()


def generate_cap(cap_name: str) -> None:
    shutil.make_archive(cap_name, 'zip', path.join(BASE_PATH, 'template_class'))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)


def generate_cap_package_class_method(package_aid: str, major: int, minor: int, class_token: int, method_token: int):
    aid = bytearray.fromhex(package_aid)
    modify_package_aid(aid, major, minor)
    modify_class_token(class_token)
    modify_method_token(method_token)

    generate_cap(f"{package_aid}_{class_token}_{method_token}.cap")


package_name = "javacardx_crypto"
aid = "A0000000620201"
major = 1
minor = 0

class_token = 0
method_token = 0
generate_cap_package_class_method(aid, major, minor, class_token, method_token)
subprocess.run(["java", "-jar", "gp.jar", "--install", f"{aid}_{class_token}_{method_token}.cap"])
subprocess.run(["java", "-jar", "gp.jar", "--uninstall", f"{aid}_{class_token}_{method_token}.cap"])