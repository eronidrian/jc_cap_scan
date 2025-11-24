import csv
import os
import subprocess
from statistics import mean

from cap_generator import generate_cap_for_package_aid
from measurement_script import measure_cap_file, uninstall_package
from trs_analyser import extract_from_single_trs_file

# for every supported package AID (except javacard.framework)
    # generate CAP file with the AID
    # repeat 100 times
        # measure time of the LOAD command
        # store result
        # uninstall file

AID_NAME_MAP = {
    "A0000000620001": "java.lang",
    "A0000000620002": "java.io",
    "A0000000620003": "java.rmi",
    "A000000062010101": "javacard.framework.service",
    "A0000000620102": "javacard.security",
    "A0000000620201": "javacardx.crypto",
    "A0000000620202": "javacardx.biometry",
    "A0000000620203": "javacardx.external",
    "A0000000620204": "javacardx.biometry1toN",
    "A0000000620205": "javacardx.security",
    "A000000062020801": "javacardx.framework.util",
    "A00000006202080101": "javacardx.framework.util.intx",
    "A000000062020802": "javacardx.framework.math",
    "A000000062020803": "javacardx.framework.tlv",
    "A000000062020804": "javacardx.framework.string",
    "A0000000620209": "javacardx.apdu",
    "A000000062020901": "javacardx.apdu.util",
    "A00000015100": "org.globalplatform",
    "A00000015102": "org.globalplatform.contactless",
    "A00000015103": "org.globalplatform.securechannel",
    "A00000015104": "org.globalplatform.securechannel.provider",
    "A00000015105": "org.globalplatform.privacy",
    "A00000015106": "org.globalplatform.filesystem",
    "A00000015107": "org.globalplatform.upgrade",
    "A0000000030000": "visa.openplatform"
}


measurements_for_one_aid = 100
major = 1
minor = 0
card_name = "nxp_jcop_241"

index_to_extract = -1

def is_installation_successful(cap_file_name: str) -> bool:
    result = subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name],
                          stdout=subprocess.PIPE)
    result = result.stdout.decode("utf-8")
    return result.find("CAP loaded") != -1


print("STARTING MEASUREMENT")
result_file = open(f"aid_list_len_{card_name}.csv", "w")
result_file_writer = csv.writer(result_file)

for aid in AID_NAME_MAP:
    cap_file_name = generate_cap_for_package_aid(bytes.fromhex(aid), major, minor, 0, AID_NAME_MAP[aid].replace(".", "_"))
    print(f"Measuring {AID_NAME_MAP[aid]}")
    supported = is_installation_successful(cap_file_name)

    if not supported:
        print(f"{AID_NAME_MAP[aid]} not supported")
        os.remove(cap_file_name)
        continue
    print(f"{AID_NAME_MAP[aid]} is supported")
    uninstall_package(cap_file_name)

    measure_cap_file(cap_file_name, measurements_for_one_aid, "tmp_traces")
    times = extract_from_single_trs_file(measurements_for_one_aid,"tmp_traces/traces_aid_list_len.trs", index_to_extract)

    mean_time = mean(times)
    print(f"AID: {aid}\n"
          f"Mean time: {mean_time}\n\n")
    result_file_writer.writerow([aid] + times)
    os.remove(cap_file_name)
    os.remove("tmp_traces/traces_aid_list_len.trs")