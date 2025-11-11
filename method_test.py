import csv
import shutil
import subprocess
import os

auth = []
auth = ["-key", "404142434445464748494A4B4C4D4E4F404142434445464748494A4B4C4D4E4F"]

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



def install_package(cap_file_name) -> int:
    message = subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    uninstall_package(cap_file_name)

    message = message.stdout.decode("utf-8") + message.stderr.decode('utf-8')

    print(f"Message: {message}")

    if message.find('Failed to communicate with card') != -1:
        return 1
    if message.find("LOAD failed: 0x6A80 (Wrong data/incorrect values in data)") != -1:
        return 2

    return 0

f = open("infineon_secora.csv", "w")
csv_writer = csv.writer(f)

for method_token in range(255):
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'rb')
    hexdata = f.read().hex().upper()
    f.close()
    hex_array = bytearray(bytes.fromhex(hexdata))

    hex_array[-1] = int(method_token)
    f = open(os.path.join('template_method', 'applets', 'javacard', 'ConstantPool.cap'), 'wb')
    f.write(hex_array)
    f.close()

    # create new cap file by zip of directories
    cap_name = f'test_{method_token}.cap'
    shutil.make_archive(cap_name, 'zip', os.path.join('template_method'))

    # remove zip suffix
    if os.path.exists(cap_name):
        os.remove(cap_name)
    os.rename(f'{cap_name}.zip', cap_name)

    result = install_package(cap_name)
    print(f"{method_token} - {result_code_map[result]}")
    csv_writer.writerow([method_token, result])

    os.remove(cap_name)

    if method_token % 5 == 0:
        print("Resetting fault counter...")
        install_package("good_package.cap")
