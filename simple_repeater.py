import subprocess
import time

package_name = "javacardx_crypto"
i = 0


def install_package(changed_byte, package_name, changed_byte_value):
    return subprocess.run(["java", "-jar", "gp.jar", "--install",
                           f"templates_{changed_byte_value}/test_{package_name}_{changed_byte}.cap",
                           "-key", "404142434445464748494A4B4C4D4E4F404142434445464748494A4B4C4D4E4F"],
                          stdout=subprocess.PIPE)


def uninstall_package(changed_byte, package_name, changed_byte_value):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           f"templates_{changed_byte_value}/test_{package_name}_{changed_byte}.cap",
                           "-key", "404142434445464748494A4B4C4D4E4F404142434445464748494A4B4C4D4E4F"],
                          stdout=subprocess.PIPE)


counter = 0
while True:
    print(counter)
    install_package(i, package_name, "ff")
    time.sleep(1)
    if counter % 1 == 0:
        install_package(9, package_name, "ff")
        uninstall_package(9, package_name, "ff")

    # subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
    #                 f"templates_ff/test_{package_name}_{i}.cap"])
    counter += 1
