import subprocess
import time

package_name = "javacardx_crypto"
i = 0

while True:
    subprocess.run(["java", "-jar", "gp.jar", "--install", f"templates_ff/test_{package_name}_{i}.cap", "-d"])
    time.sleep(1)
    subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                    f"templates_ff/test_{package_name}_{i}.cap"])
