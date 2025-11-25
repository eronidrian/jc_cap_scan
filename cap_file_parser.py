import csv
from math import ceil
from os import path, access

from api_specification import ApiSpecification, JCClass, JCMethodType
from descriptor_component_loader import load_descriptor_component, parse_type_descriptor_info, type_to_string
from import_component_loader import load_import_component
from jcAIDScan import AID_NAME_MAP

DIRECTORY = "template_class/test/javacard"

cp_info_tag_map = {
    1: "Classref",
    2: "InstanceFieldref",
    3: "VirtualMethodref",
    4: "SuperMethodref",
    5: "StaticFieldref",
    6: "StaticMethodref"
}





def is_high_bit_one(data: bytes) -> bool:
    return data[0] >= 128


def parse_class_ref(class_ref: bytes) -> JCClass | None:
    if is_high_bit_one(class_ref):
        package_token = class_ref[0] - 128
        aid = IMPORT_COMPONENT[package_token]
        class_token = class_ref[1]
        package = SPECIFICATION.get_package_by_aid(aid)
        jc_class = package.get_class_by_token(class_token)
        print(f"Package token: {package_token} (AID: {aid} - {package.name})")
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
        aid = IMPORT_COMPONENT[package_token]
        package = SPECIFICATION.get_package_by_aid(aid)
        print(f"Package token: {package_token} (AID: {aid} - {package.name})")
        print(f"Class token: {static_field_ref[1]}")
        print(f"Token: {static_field_ref[2]}")
    else:
        assert static_field_ref[0] == 0
        print(f"Internal ref offset: {int.from_bytes(static_field_ref[1:3])}")


def parse_static_method_ref(static_method_ref: bytes):
    if is_high_bit_one(static_method_ref):
        package_token = static_method_ref[0] - 128
        aid = IMPORT_COMPONENT[package_token]
        class_token = static_method_ref[1]
        package = SPECIFICATION.get_package_by_aid(aid)
        jc_class = package.get_class_by_token(class_token)
        method_token = static_method_ref[2]
        method = jc_class.get_method_by_token_and_type(method_token, JCMethodType.STATIC)

        print(f"Package token: {package_token} (AID: {aid} - {package.name})")
        print(f"Class token: {static_method_ref[1]} ({jc_class.name})")
        print(f"Token: {static_method_ref[2]} ({method.name if method is not None else 'Unknown'})")
    else:
        assert static_method_ref[0] == 0
        print(f"Internal ref offset: {int.from_bytes(static_method_ref[1:3])}")


def load_constant_pool_component(directory):
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
        print(f"Index: {i}")
        print(f"Tag: {tag} ({tag_name})")
        info = cp_info[1:]
        print(f"Info: {bytes.hex(info)}")
        if tag == 1:
            parse_class_ref_info(info)
        elif tag == 2:
            parse_instance_field_ref(info)
        elif tag == 3:
            parse_virtual_method_ref(info)
        elif tag == 4:
            parse_super_method_ref(info)
        elif tag == 5:
            parse_static_field_ref(info)
        elif tag == 6:
            parse_static_method_ref(info)
        # if JC_TYPES[i] is not None:
        #     print(f"Signature: ({JC_TYPES[i][0]}, {JC_TYPES[i][1].hex()})")
        print(f"Signature: {type_to_string(JC_TYPES[i][1], JC_TYPES[i][0], IMPORT_COMPONENT, SPECIFICATION) if JC_TYPES[i] is not None else 'not applicable'}")

        print()


SPECIFICATION = ApiSpecification.load_from_csv("/home/petr/Downloads/diplomka/jc_api_tables/overview_table_305_new.csv")

IMPORT_COMPONENT = load_import_component(DIRECTORY)
_, type_descriptor_info = load_descriptor_component(DIRECTORY)
JC_TYPES = parse_type_descriptor_info(type_descriptor_info)

load_constant_pool_component(DIRECTORY)
