from cap_parser.cap_file import CapFile
from utils.cap_file_utils import pack_directory_to_cap_file
from utils.cap_manipulation_utils import generate_cap_for_package_aid



# cap_file = CapFile.load_from_directory("templates/generic_template/test/javacard")
# cap_file.header_component.package.aid = bytearray.fromhex("ffff")

# cap_file.export_to_directory("load_enumeration/header_component/test/javacard")
f = open("load_enumeration/class_component/test/javacard/Class.cap", "rb")
content = bytearray(f.read())
content[9] = 0xff
f.close()
print(content.hex())

fw = open("load_enumeration/class_component/test/javacard/Class.cap", "wb")
fw.write(bytes(content))
fw.close()
pack_directory_to_cap_file("class_component.cap", "load_enumeration/class_component")













# header magic not checked
# directory custom components not checked