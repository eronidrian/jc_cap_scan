import csv
import re
import shutil
import subprocess
import os

from api_specification import ApiSpecification
from descriptor_component_loader import load_descriptor_component, parse_type_descriptor, string_to_type
from import_component_loader import load_import_component

auth = []
# auth = ["-key", "404142434445464748494A4B4C4D4E4F404142434445464748494A4B4C4D4E4F"]

def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def install_package(cap_file_name) -> str:
    message = subprocess.run(["java", "-jar", "gp.jar", "--install",
                              cap_file_name] + auth,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    uninstall_package(cap_file_name)

    message = message.stdout.decode("utf-8")
    message = message.replace('Warning: no keys given, using default test key 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace(
        '[WARN] GPSession - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)',
        '')
    message = message.replace('\n', ' ')

    return message


def change_method_token(method_token: int) -> None:
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[-1] = int(method_token)
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()


def pack_to_cap_file(cap_name: str, directory_name: str) -> None:
    shutil.make_archive(cap_name, 'zip', os.path.join(directory_name))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)


def bruteforce_method_tokens(method_token_range: tuple[int, int], card_name: str) -> None:
    f = open(f"{card_name}.csv", "w")
    csv_writer = csv.writer(f)

    for method_token in range(method_token_range[0], method_token_range[1]):
        change_method_token(method_token)
        # create new cap file by zip of directories
        cap_name = f'test_{method_token}.cap'
        pack_to_cap_file(cap_name, "template_method")

        result = install_package(cap_name)
        print(f"{method_token} - {result}")
        csv_writer.writerow([method_token, result])

        os.remove(cap_name)

        if method_token % 5 == 0:
            print("Resetting fault counter...")
            install_package("good_package.cap")

    f.close()


def categorise_results(card_name: str) -> None:
    f = open(f"{card_name}.csv", "r")
    csv_reader = csv.reader(f)

    f_1 = open(f"{card_name}_categories.csv", "w")
    csv_writer = csv.writer(f_1)

    categories = []

    for line in csv_reader:
        method_token = line[0]
        message = line[1].strip()
        message = re.sub(r'\{[0-9a-f]*}', r'{<hex>}', message)

        if message in categories:
            category_code = categories.index(message) + 1
        elif message == "CAP loaded":
            category_code = 0
        else:
            categories.append(message)
            category_code = categories.index(message) + 1

        csv_writer.writerow([method_token, category_code])

    print("Categories:")
    print(f"CAP loaded")
    for i, category in enumerate(categories):
        print(f"{category}")


def change_signature_in_descriptor_component(constant_pool_method_index: int, new_signature: str) -> None:
    directory = "template_method/applets/javacard"
    type_descriptor_info_start, type_descriptor_info = load_descriptor_component(directory)

    import_component = load_import_component(directory)
    specification = ApiSpecification.load_from_csv(
        "/home/petr/Downloads/diplomka/jc_api_tables/overview_table_305_new.csv")
    new_signature_jc_type = string_to_type(new_signature, import_component, specification)

    with open("template_method/applets/javacard/Descriptor.cap", "rb") as f:
        descriptor_component = f.read().hex().upper()
        descriptor_component = bytearray(bytes.fromhex(descriptor_component))

    component_size = int.from_bytes(descriptor_component[1:3])
    print(f"Descriptor component size: {component_size}")
    component_size += 100
    descriptor_component[1:3] = component_size.to_bytes(2)

    offset = 50
    descriptor_component[type_descriptor_info_start + constant_pool_method_index * 2 + 2] = offset.to_bytes(2)[0]
    descriptor_component[type_descriptor_info_start + constant_pool_method_index * 2 + 3] = offset.to_bytes(2)[1]

    descriptor_component.extend([0x00 for _ in range(100)])
    nibble_count = new_signature_jc_type[0]
    nibbles = new_signature_jc_type[1]
    descriptor_component[type_descriptor_info_start + offset] = nibble_count
    for i, nibble in enumerate(nibbles):
        descriptor_component[type_descriptor_info_start + offset + i + 1] = nibble

    with open("template_method/applets/javacard/Descriptor.cap", "wb") as f:
        f.write(descriptor_component)
        f.close()


def bruteforce_method_signature(signatures: list[str], card_name: str, method_index: int, new_method_token: int | None = None) -> None:
    f = open(f"{card_name}.csv", "w")
    csv_writer = csv.writer(f)
    for signature in signatures:
        shutil.rmtree("template_method")
        shutil.copytree("template_method_backup", "template_method")
        if new_method_token is not None:
            change_method_token(new_method_token)
        change_signature_in_descriptor_component(method_index, signature)
        pack_to_cap_file("test.cap", "template_method")
        result = install_package("test.cap")
        csv_writer.writerow([signature, result])
        print(f"{signature} - {result}")
        os.remove("test.cap")



if __name__ == "__main__":
    signatures = [
        "byte()",
        "short()",
        "short(byte[];short)",
        "void(byte[];short;short)",
        "boolean()",
        "void()",
        "void(short)",
        "short(byte[];short;short)",
        "byte[]()",
        "short(byte[];short;short;byte[];short)"
    ]
    card_name = "javacos_a_40"
    bruteforce_method_signature(signatures, card_name, 7)
    categorise_results(card_name)


