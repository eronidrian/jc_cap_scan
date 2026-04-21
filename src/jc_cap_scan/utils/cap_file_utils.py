import os
import shutil
import subprocess

GP_PATH = "src/jc_cap_scan/utils/gp.jar"
GOOD_PACKAGE_PATH = "templates/good_package.cap"
TIMEOUT = 15  # seconds


def reset_fault_counter(auth: list[str] | None = None):
    """
    Reset hypothetical fault counter on the card by installing and uninstalling a valid CAP file. If the CAP file
    cannot be installed, the process will be aborted, as it means the card is unresponsive and further operations
    would fail as well.
    :param auth: GP authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    success, result = is_installation_successful(GOOD_PACKAGE_PATH, auth)
    if not success:
        print(result)
        print("CARD UNRESPONSIVE! ABORTING!")
        exit(1)

    uninstall(GOOD_PACKAGE_PATH, auth)


def install(cap_file_name: str, auth: list[str] | None = None) -> str:
    """
    Install CAP file onto the card
    :param cap_file_name: Path to CAP file to install
    :param auth: GP authentication for the card, if needed to install CAP files onto the card
    :return: GP output stripped from unnecessary lines
    """
    if auth is None:
        message = subprocess.run(["java", "-jar", GP_PATH, "--install",
                                  cap_file_name],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    else:
        message = subprocess.run(["java", "-jar", GP_PATH, "--install",
                                  cap_file_name] + auth,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)

    # remove lines without much added value
    message = message.stdout.decode("utf-8")
    message = message.replace('# Warning: no keys given, defaulting to 404142434445464748494A4B4C4D4E4F', '')
    message = message.replace("Warning: no keys given, using default test key 404142434445464748494A4B4C4D4E4F", '')
    message = message.replace(
        '[WARN] GPSession - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)',
        '')
    message = message.replace(
        "[WARN] GlobalPlatform - GET STATUS failed for 80F21000024F0000 with 0x6A81 (Function not supported e.g. card Life Cycle State is CARD_LOCKED)",
        "")
    message = message.replace('\n', ' ')
    message = message.strip()

    if message == f"{cap_file_name} loaded: test 73696D706C65":
        message = "CAP loaded"

    return message


def is_installation_successful(cap_file_name: str, auth: list[str] | None = None) -> tuple[bool, str]:
    """
    Find out whether the CAP file can be installed successfully
    :param cap_file_name: Path to CAP file to install
    :param auth: GP authentication for the card, if needed to install CAP files onto the card
    :return:
    """
    result = install(cap_file_name, auth)
    uninstall(cap_file_name, auth)
    return result.find(f"CAP loaded") != -1, result


def uninstall(cap_file_name: str, auth: list[str] | None = None) -> str:
    if auth is None:
        result = subprocess.run(["java", "-jar", GP_PATH, "--uninstall",
                                 cap_file_name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    else:
        result = subprocess.run(["java", "-jar", GP_PATH, "--uninstall",
                                 cap_file_name] + auth,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    return result.stdout.decode("utf-8")


def call(debug: bool = False, auth: list[str] | None = None) -> str:
    command_apdu = "12340000"
    if auth is None:
        call_response_lines = subprocess.run(["java", "-jar", GP_PATH, "--apdu",
                                              "00A404000C73696D706C656170706C657400", "--apdu", command_apdu,
                                              "-d"],
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
    else:
        call_response_lines = subprocess.run(["java", "-jar", GP_PATH, "--apdu",
                                              "00A404000C73696D706C656170706C657400", "--apdu", command_apdu,
                                              "-d"] + auth,
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
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
