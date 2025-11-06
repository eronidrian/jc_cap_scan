import csv
import shutil
import subprocess
import os

def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def install_package(cap_file_name) -> bool:
    # subprocess.run(["java", "-jar", "gp.jar", "--info"],
    #                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    success = False
    result = subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    result = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
    print(result)
    if result.find("Failed") == -1:
        success = True

    uninstall_package(cap_file_name)

    return success

# f = open("method_results.csv", "w")
# csv_writer = csv.writer(f)
# for i in range(5):
#     row = []
#     for method_token in range(20):

method_token = 5

print(method_token)
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

# row.append(install_package(cap_name))
print()
print()
# os.remove(cap_name)
    # csv_writer.writerow(row)
    # print(row)