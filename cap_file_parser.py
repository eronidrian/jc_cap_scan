import csv
from math import ceil
from os import path, access

from api_specification import ApiSpecification, JCClass, JCMethodType
from jcAIDScan import AID_NAME_MAP

directory = "template_method/applets/javacard"

cp_info_tag_map = {
    1 : "Classref",
    2 : "InstanceFieldref",
    3 : "VirtualMethodref",
    4 : "SuperMethodref",
    5 : "StaticFieldref",
    6 : "StaticMethodref"
}


def load_import_component() -> list[str]:
    with open(path.join(directory, "Import.cap"), "rb") as f:
        import_component = f.read()

    count = import_component[3]
    packages = import_component[4:]

    start = 0
    aids = []
    for _ in range(count):
        minor_version = packages[start]
        major_version = packages[start + 1]
        aid_len = packages[start + 2]
        aid = packages[start + 3 : start + 3 + aid_len].hex().upper()
        start = start + 3 + aid_len
        aids.append(aid)
        # print(f"Minor version: {minor_version}")
        # print(f"Major version: {major_version}")
        # print(f"AID: {aid}")
        # print()
    return aids

def parse_type_descriptor(type_descriptor: bytes) -> tuple[int, bytes]:
    nibble_count = type_descriptor[0]
    jc_type = type_descriptor[1 : int((nibble_count + 1) / 2) + 1]
    return nibble_count, jc_type

def load_descriptor_component() -> list[bytes]:
    with open(path.join(directory, "Descriptor.cap"), "rb") as f:
        descriptor_component = f.read()

    class_count = descriptor_component[3]
    descriptor_component = descriptor_component[4:]

    start = 0
    for _ in range(class_count):
        interface_count = descriptor_component[start + 4]
        field_count = int.from_bytes(descriptor_component[start + 5 : start + 7])
        method_count = int.from_bytes(descriptor_component[start + 7: start + 9])

        field_descriptor_info_len = 7
        method_descriptor_info_len = 12
        start = start + 9 + interface_count * 2 + field_count * field_descriptor_info_len + method_count * method_descriptor_info_len

    type_descriptor_info = descriptor_component[start:]
    constant_pool_count = int.from_bytes(type_descriptor_info[ : 2])
    print(f"Constant pool count: {constant_pool_count}\n")

    jc_types = []
    for i in range(2, constant_pool_count * 2 + 1, 2):
        offset = int.from_bytes(type_descriptor_info[i : i + 2])
        if offset != 0xffff:
            jc_types.append(parse_type_descriptor(type_descriptor_info[offset:]))
        else:
            jc_types.append(None)

    return jc_types




def is_high_bit_one(data: bytes) -> bool:
    return data[0] >= 128

def parse_class_ref(class_ref: bytes) -> JCClass | None:
    if is_high_bit_one(class_ref):
        package_token = class_ref[0] - 128
        aid = AIDS[package_token]
        class_token = class_ref[1]
        jc_class = SPECIFICATION.get_package_by_aid(aid).get_class_by_token(class_token)
        print(f"Package token: {package_token} (AID: {AIDS[package_token]} - {AID_NAME_MAP[AIDS[package_token]]})")
        print(f"Class token: {class_ref[1]} ({jc_class.name})")
        return jc_class
    print(f"Internal class ref: {int.from_bytes(class_ref)}")
    return None


def parse_class_ref_info(class_ref_info: bytes):
    assert class_ref_info[2] == 0
    parse_class_ref(class_ref_info[:2])


def parse_instance_field_ref(instance_field_ref: bytes):
    jc_class = parse_class_ref(instance_field_ref[:2])
    if jc_class is None:
        print(f"Token: {instance_field_ref[2]}")
    else:
        token = instance_field_ref[2]
        method = jc_class.get_method_by_token_and_type(token, JCMethodType.VIRTUAL)
        print(f"Token: {instance_field_ref[2]} ({method.name if method is not None else 'Unknown'})")



def parse_virtual_method_ref(virtual_method_ref: bytes):
    parse_instance_field_ref(virtual_method_ref)

def parse_super_method_ref(super_method_ref: bytes):
    parse_instance_field_ref(super_method_ref)


def parse_static_field_ref(static_field_ref: bytes):
    if is_high_bit_one(static_field_ref):
        package_token = static_field_ref[0] - 128
        print(f"Package token: {package_token} (AID: {AIDS[package_token]} - {AID_NAME_MAP[AIDS[package_token]]})")
        print(f"Class token: {static_field_ref[1]}")
        print(f"Token: {static_field_ref[2]}")
    else:
        assert static_field_ref[0] == 0
        print(f"Internal ref offset: {int.from_bytes(static_field_ref[1:3])}")

def parse_static_method_ref(static_method_ref: bytes):
    if is_high_bit_one(static_method_ref):
        package_token = static_method_ref[0] - 128
        aid = AIDS[package_token]
        class_token = static_method_ref[1]
        jc_class = SPECIFICATION.get_package_by_aid(aid).get_class_by_token(class_token)
        method_token = static_method_ref[2]
        method = jc_class.get_method_by_token_and_type(method_token, JCMethodType.STATIC)
        print(f"Package token: {package_token} (AID: {AIDS[package_token]} - {AID_NAME_MAP[AIDS[package_token]]})")
        print(f"Class token: {static_method_ref[1]} ({jc_class.name})")
        print(f"Token: {static_method_ref[2]} ({method.name if method is not None else 'Unknown'})")
    else:
        assert static_method_ref[0] == 0
        print(f"Internal ref offset: {int.from_bytes(static_method_ref[1:3])}")


def type_to_string(jc_type: tuple[int, bytes]) -> str:
    type_to_string_map = {
        "0" : "",
        "1" : "void",
        "2" : "boolean",
        "3" : "byte",
        "4" : "short",
        "5" : "int",
        "6" : "reference",
        "a" : "boolean[]",
        "b" : "byte[]",
        "c" : "short[]",
        "d" : "int[]",
        "e" : "reference[]"
    }
    jc_type_len = jc_type[0]
    jc_type = jc_type[1]
    jc_type = jc_type.hex()
    jc_type = jc_type if jc_type_len % 2 == 0 else jc_type[:-1]
    type_strings = []
    i = 0
    while i < len(jc_type):
        type_string = type_to_string_map.get(jc_type[i], "?")
        if "reference" in type_string:
            reference = jc_type[i + 1: i + 5]
            package_token = int(reference[:2], 16) - 128
            package_aid = AIDS[package_token]
            package = SPECIFICATION.get_package_by_aid(package_aid)
            class_token = int(reference[2:], 16)
            jc_class = package.get_class_by_token(class_token)

            if '[]' in type_string:
                reference_string = f"{package.name}.{jc_class.name}[]"
            else:
                reference_string = f"{package.name}.{jc_class.name}"

            type_strings.append(reference_string)
            i += 5
        else:
            type_strings.append(type_string)
            i += 1


    return f"{type_strings[-1]}({','.join(type_strings[:-1])})"

def load_constant_pool_component():
    with open(path.join(directory, "ConstantPool.cap"), "rb") as f:
        constant_pool_component = f.read()

    print(f"Tag: {constant_pool_component[0]}")
    print(f"Size: {int.from_bytes(constant_pool_component[1:3])}")
    count = int.from_bytes(constant_pool_component[3:5])
    print(f"Count: {count}")
    print()

    constant_pool = constant_pool_component[5:]
    for i in range(count):
        cp_info = constant_pool[i * 4:(i + 1) * 4]
        tag = cp_info[0]
        tag_name = cp_info_tag_map.get(tag, "Unknown")
        print(f"Tag: {tag} ({tag_name})")
        info = cp_info[1:]
        print(f"Info: {bytes.hex(info)}")
        if tag == 1:
            parse_class_ref_info(info)
        elif tag == 2:
            continue
            parse_instance_field_ref(info)
        elif tag == 3:
            parse_virtual_method_ref(info)
        elif tag == 4:
            parse_super_method_ref(info)
        elif tag == 5:
            parse_static_field_ref(info)
        elif tag == 6:
            parse_static_method_ref(info)
        print(f"Signature: {type_to_string(JC_TYPES[i]) if JC_TYPES[i] is not None else 'not applicable'}")

        print()

SPECIFICATION = ApiSpecification.load_from_csv("/home/petr/Downloads/diplomka/jc_api_tables/overview_table_305_new.csv")

AIDS = load_import_component()
JC_TYPES = load_descriptor_component()

load_constant_pool_component()

