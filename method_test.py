import csv
import re
import shutil
import subprocess
import os

auth = []
# auth = ["-key", "404142434445464748494A4B4C4D4E4F404142434445464748494A4B4C4D4E4F"]

def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)

result_code_map = {
    0 : "Method with this token and signature exists",
    1 : "Method exists but has a different signature",
    2 : "Method does not exist",
    3 : "Undefined"
}



def install_package(cap_file_name) -> str:
    message = subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    uninstall_package(cap_file_name)

    message = message.stdout.decode("utf-8")
    message = message.replace('Warning: no keys given, using default test key 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace('\n', ' ')

    # print(f"Message: {message}")

    return message

# f = open("javacos_a_40.csv", "w")
# csv_writer = csv.writer(f)
#
# for method_token in range(255):
#     f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'rb')
#     hexdata = f.read().hex().upper()
#     f.close()
#     hex_array = bytearray(bytes.fromhex(hexdata))
#
#     hex_array[-1] = int(method_token)
#     f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'wb')
#     f.write(hex_array)
#     f.close()
#
#     # create new cap file by zip of directories
#     cap_name = f'test_{method_token}.cap'
#     shutil.make_archive(cap_name, 'zip', os.path.join('template_method'))
#
#     # remove zip suffix
#     if os.path.exists(cap_name):
#         os.remove(cap_name)
#     os.rename(f'{cap_name}.zip', cap_name)
#
#     result = install_package(cap_name)
#     print(f"{method_token} - {result}")
#     csv_writer.writerow([method_token, result])
#
#     os.remove(cap_name)
#
#     if method_token % 5 == 0:
#         print("Resetting fault counter...")
#         install_package("good_package.cap")

card_name = "javacos_a_40"
f = open(f"{card_name}.csv", "r")
csv_reader = csv.reader(f)

f_1 = open(f"{card_name}_categories.csv", "w")
csv_writer = csv.writer(f_1)

categories = []

for line in csv_reader:
    method_token = line[0]
    message = line[1].strip()
    message = re.sub(r'\{[0-9a-f]*\}', r'{<hex>}', message)

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

