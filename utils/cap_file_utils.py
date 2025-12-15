import os
import shutil
import subprocess


def install(cap_file_name: str, auth: list[str] | None = None) -> str:
    if auth is None:
        result = subprocess.run(["java", "-jar", "gp.jar", "--install",
                                 cap_file_name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        result = subprocess.run(["java", "-jar", "gp.jar", "--install",
                                 cap_file_name] + auth,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.decode("utf-8")


def is_installation_successful(cap_file_name: str, auth: list[str] | None = None) -> bool:
    result = install(cap_file_name, auth)
    return result.find("CAP loaded") != -1


def uninstall(cap_file_name: str, auth: list[str] | None = None) -> str:
    if auth is None:
        result = subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                                 cap_file_name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        result = subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                                 cap_file_name] + auth,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.decode("utf-8")

def pack_directory_to_cap_file(cap_file_name: str, directory_name: str) -> None:
    shutil.make_archive(cap_file_name, 'zip', os.path.join(directory_name))

    if os.path.exists(cap_file_name):
        os.remove(cap_file_name)
    os.rename(f'{cap_file_name}.zip', cap_file_name)
