from cap_parser.cap_file import CapFile
from utils.cap_file_utils import pack_directory_to_cap_file
from utils.cap_manipulation_utils import generate_cap_for_package_aid



# cap_file = CapFile.load_from_directory("templates/generic_template/test/javacard")
# cap_file.header_component.package.aid = bytearray.fromhex("ffff")

# cap_file.export_to_directory("load_enumeration/header_component/test/javacard")
# f = open("load_enumeration/generic_template/test/javacard/Header.cap", "rb")
# content = bytearray(f.read())
# content[2] = 0
# print(content.hex())
#
# fw = open("load_enumeration/generic_template/test/javacard/Header.cap", "wb")
# fw.write(content)
pack_directory_to_cap_file("header_component.cap", "load_enumeration/generic_template")













# header magic not checked