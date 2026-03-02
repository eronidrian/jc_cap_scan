import os
import re
import shutil
import subprocess

from measurement_script import measure_cap_file_install

NUM_OF_MEASUREMENTS = 1

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


def test_class_token_range(aid: bytearray, major: int, minor: int, class_token_range: tuple[int, int]):
    # result_file = open(f"nxp_jcop_4_{aid.hex().upper()}.csv", "w")
    # csv_writer = csv.writer(result_file)
    for class_token in range(class_token_range[0], class_token_range[1]):
        cap_name = generate_cap_for_aid_and_class_token(aid, major, minor, class_token)
        measure_cap_file_install(cap_name, NUM_OF_MEASUREMENTS, "traces")
        os.remove(cap_name)
    # extract times
    # store results


aid = bytearray.fromhex("A0000000620102")
major = 1
minor = 0


test_class_token_range(aid, major, minor, (0, 1))

