from os import path



#returns list of jc_types
def parse_type_descriptor_info(type_descriptor_info: bytes) -> list[tuple[int, bytes]]:
    constant_pool_count = int.from_bytes(type_descriptor_info[: 2])
    print(f"Constant pool count: {constant_pool_count}\n")

    jc_types = []
    for i in range(2, constant_pool_count * 2 + 1, 2):
        offset = int.from_bytes(type_descriptor_info[i: i + 2])
        if offset != 0xffff:
            jc_types.append(parse_type_descriptor(type_descriptor_info[offset:]))
        else:
            jc_types.append(None)

    return jc_types


# returns where type_descriptor_info starts and its bytes
def load_descriptor_component(directory: str) -> tuple[int, bytes]:
    with open(path.join(directory, "Descriptor.cap"), "rb") as f:
        descriptor_component = f.read()

    class_count = descriptor_component[3]
    descriptor_component = descriptor_component[4:]

    start = 0
    for _ in range(class_count):
        interface_count = descriptor_component[start + 4]
        field_count = int.from_bytes(descriptor_component[start + 5: start + 7])
        method_count = int.from_bytes(descriptor_component[start + 7: start + 9])

        field_descriptor_info_len = 7
        method_descriptor_info_len = 12
        start = start + 9 + interface_count * 2 + field_count * field_descriptor_info_len + method_count * method_descriptor_info_len

    type_descriptor_info = descriptor_component[start:]
    return start + 4, type_descriptor_info

import re



def parse_type_descriptor(type_descriptor: bytes) -> tuple[int, bytes]:
    nibble_count = type_descriptor[0]
    jc_type = type_descriptor[1: int((nibble_count + 1) / 2) + 1]
    return nibble_count, jc_type

type_to_string_map = {
        "0": "",
        "1": "void",
        "2": "boolean",
        "3": "byte",
        "4": "short",
        "5": "int",
        "6": "reference",
        "a": "boolean[]",
        "b": "byte[]",
        "c": "short[]",
        "d": "int[]",
        "e": "reference[]"
    }

def type_to_string(jc_type: bytes, jc_type_len: int, import_component, specification) -> str:
    jc_type = jc_type.hex()
    jc_type = jc_type if jc_type_len % 2 == 0 else jc_type[:-1]
    type_strings = []
    i = 0
    while i < len(jc_type):
        type_string = type_to_string_map.get(jc_type[i], "?")
        if "reference" in type_string:
            reference = jc_type[i + 1: i + 5]
            package_token = int(reference[:2], 16) - 128
            package_aid = import_component[package_token]
            package = specification.get_package_by_aid(package_aid)
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

    return f"{type_strings[-1]}({';'.join(type_strings[:-1])})"

string_to_type_map = dict((v, k) for k, v in type_to_string_map.items())
string_to_type_map[""] = ""

def reference_name_to_reference(reference_name: str, import_component, specification) -> str:
    reference_name_split =  reference_name.split(".")
    class_name = reference_name_split[-1]
    package_name = ".".join(reference_name_split[:-1])

    package = specification.get_package_by_name(package_name)
    if package is None:
        raise ValueError(f"Package with name {package_name} not found in specification")
    try:
        package_token = import_component.index(package.aid)
    except ValueError:
        raise ValueError(f"Package with AID {package.aid} not found in Import component")

    jc_class = package.get_class_by_name(class_name)
    if jc_class is None:
        raise ValueError(f"Class with name {class_name} not found in the specification")

    hex_package_token = hex(package_token + 128)[2:]
    hex_class_token = hex(jc_class.token)[2:].zfill(2)

    return hex_package_token + hex_class_token


def string_to_type(signature_string: str, import_component, specification) -> tuple[int, bytes]:
    result = re.search(r'(.*)\((.*)\)', signature_string)
    return_value = result.group(1)
    parameters = result.group(2)
    parameters = parameters.split(";")
    type_strings = parameters + [return_value]
    jc_type = ""
    for type_string in type_strings:
        if type_string in string_to_type_map.keys():
            jc_type += string_to_type_map[type_string]
        elif re.match(r'[.a-zA-Z$]+\[]', type_string):
            jc_type += string_to_type_map["reference[]"]
            jc_type += reference_name_to_reference(type_string[:-2], import_component, specification)
        elif re.match(r'[.a-zA-Z$]+', type_string):
            jc_type += string_to_type_map["reference"]
            jc_type += reference_name_to_reference(type_string, import_component, specification)
        else:
            raise ValueError(f"Unrecognized type string: {type_string}")

    jc_type_len = len(jc_type)
    jc_type = jc_type if jc_type_len % 2 == 0 else jc_type + "0"

    return jc_type_len, bytes.fromhex(jc_type)


# TESTS = [
#     ["void(javacard.security.Key;byte)", (7, 0x68100310)],
#     ["javacard.security.Signature(byte;boolean)", (7, 0x326810f0)],
#     ["javacard.security.PrivateKey()", (5, 0x681020)],
#     ["void()", (1, 0x10)],
#     ["void(byte;short)", (3, 0x3410)],
#     ["void(javacard.framework.APDU)", (6, 0x6800a1)],
#     ["void(byte[];short;byte)", (4, 0xb431)]
# ]

# SPECIFICATION = ApiSpecification.load_from_csv("/home/petr/Downloads/diplomka/jc_api_tables/overview_table_305_new.csv")
#
# IMPORT_COMPONENT = load_import_component(directory="template_method/applets/javacard")
#
# for test in TESTS:
#     test_case = test[0]
#     print(f"Test case: {test_case}")
#     expected = test[1]
#     print(f"Expected: ({expected[0], hex(expected[1])[2:]})")
#     received = string_to_type(test_case, IMPORT_COMPONENT, SPECIFICATION)
#     received = (received[0], received[1].hex())
#     print(f"Received: {received}")
#     assert expected[0] == received[0]
#     assert hex(expected[1])[2:] == received[1]