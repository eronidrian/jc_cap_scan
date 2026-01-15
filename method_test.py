import csv
import re
import shutil
import subprocess
import os

from cap_parser.cap_file import CapFile


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
    # uninstall_package(cap_file_name)

    message = message.stdout.decode("utf-8")
    message = message.replace('Warning: no keys given, using default test key 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace(
        '[WARN] GPSession - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)',
        '')
    message = message.replace('\n', ' ')
    message = message.strip()

    return message

def call_package(debug: bool = False) -> str:
    command_apdu = "12340000"
    call_response_lines = subprocess.run(["java", "-jar", "gp.jar", "--apdu",
                                          "00A404000C73696D706C656170706C657400", "--apdu", command_apdu,
                                          "-d"] + auth,
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    call_response_lines = call_response_lines.stdout.decode("utf-8").splitlines()

    if debug:
        for i in range(len(call_response_lines)):
            print(i, call_response_lines[i])

    command_line_num = 0
    for i, line in enumerate(call_response_lines):
        if command_apdu in line:
            command_line_num = i
            break
    response_line_num = command_line_num + 1
    call_response = call_response_lines[response_line_num].split(")")[-1].strip()

    return call_response


def change_method_token(method_token: int) -> None:
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[36] = int(method_token)
    # hex_array[-1] = int(method_token)
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()


def pack_directory_to_cap_file(cap_name: str, directory_name: str) -> None:
    shutil.make_archive(cap_name, 'zip', os.path.join(directory_name))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)


def bruteforce_method_tokens(method_token_range: list[int], card_name: str) -> None:
    f = open(f"{card_name}.csv", "w")
    csv_writer = csv.writer(f)

    for method_token in method_token_range:
        change_method_token(method_token)
        # create new cap file by zip of directories
        cap_name = f'test_{method_token}.cap'
        pack_directory_to_cap_file(cap_name, "template_method")

        install_response = install_package(cap_name)
        call_response = ""
        if "CAP loaded" in install_response:
            call_response_lines = subprocess.run(["java", "-jar", "gp.jar", "--apdu",
                                                  "00A404000C73696D706C656170706C657400", "--apdu", "12340000",
                                                  "-d"] + auth,
                                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            call_response_lines = call_response_lines.stdout.decode("utf-8").splitlines()
            for i in range(len(call_response_lines)):
                print(i, call_response_lines[i])

            # print(f"{call_response_lines[10]}")
            # print(f"{call_response_lines[11]}")
            call_response = call_response_lines[11].split(")")[-1].strip()

        print(f"{method_token} - {install_response} - {call_response}")
        uninstall_package(cap_name)
        csv_writer.writerow([method_token, install_response, call_response])

        os.remove(cap_name)

        if method_token % 5 == 0:
            print("Resetting fault counter...")
            install_package("good_package.cap")
            uninstall_package("good_package.cap")

    f.close()


def categorise_results(card_name: str) -> None:
    f = open(f"{card_name}.csv", "r")
    csv_reader = csv.reader(f)

    f_1 = open(f"{card_name}_categories.csv", "w")
    csv_writer = csv.writer(f_1)

    categories = []

    for line in csv_reader:
        method_token = line[0]
        message = line[1].strip() + " " + line[2].strip()
        message = re.sub(r'\{[0-9a-f]*}', r'{<hex>}', message)

        if message in categories:
            category_code = categories.index(message)
        else:
            categories.append(message)
            category_code = categories.index(message)

        csv_writer.writerow([method_token, category_code])

    print("Categories:")
    for i, category in enumerate(categories):
        print(f"{category}")

def is_template_correct(template_location: str) -> bool:
    cap_name = "template_test.cap"
    pack_directory_to_cap_file(cap_name, template_location)

    install_response = install_package(cap_name)
    if "CAP loaded" not in install_response:
        print(f"Template {template_location} did not install successfully")
        print(f"Response: {install_response}")
        return False

    call_response = call_package(debug=True)
    if "9000" not in call_response:
        print(f"Template {template_location} cannot be called successfully")
        print(f"Response: {call_response}")
        return False

    uninstall_package(cap_name)
    # os.remove(cap_name)
    return True

def reset_fault_counter() -> None:
    install_package("good_package.cap")
    uninstall_package("good_package.cap")

def method_test(card_name: str) -> None:
    for entry in os.scandir("templates"):
        if not entry.is_dir():
            continue

        _, static_or_virtual, class_name, method_name, return_or_call = entry.name.split("_")
        print(f"Testing template {entry.name}")
        if not is_template_correct(entry.path):
            print(f"Skipping template {entry.name}")
            continue

        result_file = open(f"{card_name}_{entry.name}.csv", "w")
        csv_writer = csv.writer(result_file)

        template_loaded = CapFile.load_from_directory(os.path.join(entry.path, "applets", "javacard"))
        constant_pool_entry = template_loaded.constant_pool_component.get_cp_info_by_method_name(method_name)
        for method_token in range(256):
            constant_pool_entry.info.token = method_token
            template_loaded.export_to_directory(f"{entry.name}_{method_token}")
            cap_file_name = f"{entry.name}_{method_token}.cap"
            pack_directory_to_cap_file(cap_file_name, f"{entry.name}_{method_token}")

            install_response = install_package(cap_file_name)
            call_response = ""
            if "CAP loaded" in install_response:
                call_response = call_package()

            print(f"{method_token} - {install_response} - {call_response}")
            csv_writer.writerow([method_token, install_response, call_response])
            uninstall_package(cap_file_name)

            if method_token % 5 == 0:
                print("Resetting fault counter...")
                reset_fault_counter()
            # os.remove(cap_file_name)
            # shutil.rmtree(f"{entry.name}_{method_token}")


if __name__ == "__main__":
    card_name = "javacos_a_40"

    method_test(card_name)

    # token_list = []
    #
    # bruteforce_method_tokens(token_list, card_name)
    # categorise_results(card_name)

    # cap_file = CapFile.load_from_directory("template_method/applets/javacard")
    # cap_file.constant_pool_component.pretty_print()


# iterate over templates in 'templates' directory
    # for each
        # verify that unchanged templates installs without problem
        # locate method entry in ConstantPool component
        # bruteforce all method tokens
        # store results
