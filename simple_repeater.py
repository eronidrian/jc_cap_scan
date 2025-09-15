import subprocess
import time

package_name = "javacardx_crypto"
i = 0
counter = 0

while True:
    print(counter)
    subprocess.run(["java", "-jar", "gp.jar", "--install", f"templates_ff/test_{package_name}_{i}.cap"])
    time.sleep(1)
    if counter % 10 == 0:
        subprocess.run(["java", "-jar", "gp.jar", "--install", f"templates_ff/test_{package_name}_9.cap"])
        subprocess.run(["java", "-jar", "gp.jar", "--uninstall", f"templates_ff/test_{package_name}_9.cap"])

    # subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
    #                 f"templates_ff/test_{package_name}_{i}.cap"])
    counter += 1