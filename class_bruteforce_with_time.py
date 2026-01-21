import csv
import os
import re
import shutil
import subprocess

from api_specification import ApiSpecification


class PackageAID:
    aid = []
    major = 0
    minor = 0

    def __init__(self, aid, major, minor):
        self.aid = aid
        self.major = major
        self.minor = minor

    def get_length(self):
        return len(self.aid) + 1 + 1 + 1

    def serialize(self):
        aid_str = ''.join('{:02X}'.format(a) for a in self.aid)
        # one package format: package_major package_minor package_len package_AID
        serialized = '{:02X}{:02X}{:02X}{}'.format(self.minor, self.major, len(self.aid), aid_str)
        return serialized

    def get_aid_hex(self):
        return bytes(self.aid).hex()  # will be in lowercase


def format_import(aid: bytes, major: int, minor: int):
    javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 0)

    imported_packages = []
    imported_packages.append(javacard_framework)
    # imported_packages.append(java_lang)  # do not import java_lang as default (some cards will then fail to load)
    imported_packages.append(PackageAID(aid, major, minor))

    total_len = 1  # include count of number of packages
    for package in imported_packages:
        total_len += package.get_length()

    # format of Import.cap: 04 00 len num_packages package1 package2 ... packageN
    import_section = '0400{:02x}{:02x}'.format(total_len, len(imported_packages))

    # serialize all packages
    for package in imported_packages:
        import_section += package.serialize()

    f = open(os.path.join('template_class', 'test', 'javacard', 'Import.cap'), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()


def format_constant_pool(class_token: int):
    f = open(os.path.join('template_class', 'test', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[41] = 1
    hex_array[43] = int(class_token)
    f = open(os.path.join('template_class', 'test', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()


def generate_cap_for_aid_and_class_token(aid: bytearray, major: int, minor: int, class_token: int) -> str:
    format_import(aid, major, minor)
    format_constant_pool(class_token)

    # create new cap file by zip of directories
    cap_name = f'test_{aid.hex()}_{class_token}.cap'
    shutil.make_archive(cap_name, 'zip', os.path.join('template_class'))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)

    return cap_name

def extract_load_time(gp_log: str) -> tuple[int, int]:
    gp_log = gp_log.splitlines()
    load_line = gp_log[23]
    match_1 = re.search(r'([0-9]+)ns', load_line)

    load_line = gp_log[25]
    match_2 = re.search(r'([0-9]+)ns', load_line)

    for i in range(len(gp_log)):
        print(i, gp_log[i])

    if match_1 is None and match_2 is None:
        for i in range(len(gp_log)):
            print(i, gp_log[i])
        exit(1)
    if match_1 is None:
        return 0, match_2.group(1)
    if match_2 is None:
        return match_1.group(1), 0
    return match_1.group(1), match_2.group(1)



def install_package(cap_file_name) -> tuple[bool, tuple[int, int]]:
    success = False
    result = subprocess.run(["java", "-jar", "gp_precise.jar", "--install",
                           cap_file_name, "-d"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    result = result.stdout.decode("utf-8")
    duration = extract_load_time(result)
    if result.find("0x6A80") == -1 and result.find("0x6985") == -1:
        success = True
    uninstall_package(cap_file_name)

    return success, duration


def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_aid_and_class_token(aid: bytearray, major: int, minor: int, class_token: int) -> tuple[bool, tuple[int, int]]:
    cap_name = generate_cap_for_aid_and_class_token(aid, major, minor, class_token)
    result, duration = install_package(cap_name)
    os.remove(cap_name)
    return result, duration

def test_class_token_range(aid: bytearray, major: int, minor: int, class_token_range: tuple[int, int]):
    result_file = open(f"nxp_jcop_4_{aid.hex().upper()}.csv", "w")
    csv_writer = csv.writer(result_file)
    for class_token in range(class_token_range[0], class_token_range[1]):
        durations_1 = []
        durations_2 = []
        for _ in range(100):
            result, duration = test_aid_and_class_token(aid, major, minor, class_token)
            print(f"class token: {class_token}, success: {result}, duration_1: {duration[0]}, duration_2: {duration[1]}\n\n")
            durations_1.append(duration[0])
            durations_2.append(duration[1])
        csv_writer.writerow([class_token] + durations_1)
        csv_writer.writerow([class_token] + durations_2)


aid = bytearray.fromhex("A0000000620102")
major = 1
minor = 0
class_token = 18


# test_aid_and_class_token(aid, major, minor, class_token)
# # generate_cap_for_aid_and_class_token(aid, major, minor, class_token)


test_class_token_range(aid, major, minor, (31, 256))

