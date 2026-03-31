import os
import shutil
import subprocess

GP_PATH = "src/jc_cap_scan/utils/gp.jar"
GOOD_PACKAGE_PATH = "templates/good_package.cap"

def reset_fault_counter(auth: list[str] | None = None):
    success, result = is_installation_successful(GOOD_PACKAGE_PATH, auth)
    if not success:
        print(result)
        print("CARD UNRESPONSIVE! ABORTING!")
        exit(1)

    uninstall(GOOD_PACKAGE_PATH, auth)


def install(cap_file_name: str, auth: list[str] | None = None) -> str:
    if auth is None:
        message = subprocess.run(["java", "-jar", GP_PATH, "--install",
                                  cap_file_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        message = subprocess.run(["java", "-jar", GP_PATH, "--install",
                                  cap_file_name] + auth,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # remove lines without much added value
    message = message.stdout.decode("utf-8")
    message = message.replace('# Warning: no keys given, defaulting to 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace(
        '[WARN] GPSession - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)',
        '')
    message = message.replace('\n', ' ')
    message = message.strip()

    return message


def is_installation_successful(cap_file_name: str, auth: list[str] | None = None) -> tuple[bool, str]:
    result = install(cap_file_name, auth)
    uninstall(cap_file_name, auth)
    return result.find(f"{cap_file_name} loaded") != -1, result


def uninstall(cap_file_name: str, auth: list[str] | None = None) -> str:
    if auth is None:
        result = subprocess.run(["java", "-jar", GP_PATH, "--uninstall",
                                 cap_file_name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        result = subprocess.run(["java", "-jar", GP_PATH, "--uninstall",
                                 cap_file_name] + auth,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout.decode("utf-8")


def call(debug: bool = False, auth: list[str] | None = None) -> str:
    command_apdu = "12340000"
    call_response_lines = subprocess.run(["java", "-jar", GP_PATH, "--apdu",
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


def pack_directory_to_cap_file(cap_file_name: str, directory_name: str) -> None:
    shutil.make_archive(cap_file_name, 'zip', directory_name)

    if os.path.exists(cap_file_name):
        print("CAP file with the same name already exists")
        exit(1)
    os.rename(f'{cap_file_name}.zip', cap_file_name)
