# from cap_parser.cap_file import CapFile
# from cap_parser.import_component import PackageInfo
# from utils.cap_file_utils import pack_directory_to_cap_file
# from utils.cap_manipulation_utils import generate_cap_for_package_aid
#
#
#
# cap_file = CapFile.load_from_directory("templates/generic_template/test/javacard")
# print(cap_file.import_component.packages[0])
# print(cap_file.import_component.packages[1])
# cap_file.import_component.packages.append(PackageInfo(cap_file, 0, 1, bytes.fromhex("A000000062FF01")))
# cap_file.export_to_directory("load_enumeration/import_A000000062FF01/test/javacard")
#
# # cap_file.header_component.package.aid = bytearray.f   romhex("ffff")
#
# # cap_file.export_to_directory("load_enumeration/header_component/test/javacard")
# # f = open("load_enumeration/staticfield_component/test/javacard/StaticField.cap", "rb")
# # content = bytearray(f.read())
# # content[2] = 0x00
# # f.close()
# # print(content.hex())
# #
# # fw = open("load_enumeration/staticfield_component/test/javacard/StaticField.cap", "wb")
# # fw.write(bytes(content))
# # fw.close()
# pack_directory_to_cap_file("load_enumeration/import_A000000062FF01.cap", "load_enumeration/import_A000000062FF01")
#
#
#
#
#
#
#
#
#
#
#
# # header magic not checked
# # directory custom components not checked
import csv

from config import Config
from trs_analysis.trs_extractor import extract_times_from_trs_file

config = Config.load_from_toml("javacos_a_40_config.toml")
f = open("results.csv", "w")
csv_writer = csv.writer(f)

for byte_number in range(9):
    aid = bytearray.fromhex("a00000006202080101")
    aid[byte_number] = 255
    filename = f"traces/test_{aid.hex()}.trs"
    print(filename)
    times = extract_times_from_trs_file(filename, config.extraction)
    print(times)
    csv_writer.writerow([byte_number + 1] + times)
