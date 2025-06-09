import subprocess

package_name = "javacardx_crypto"
i = 0

while True:
    subprocess.run(["java", "-jar", "gp.jar", "--install", f"templates_ff/test_{package_name}_{i}.cap"])