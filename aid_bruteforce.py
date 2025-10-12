import csv
import os
from statistics import median

from aid_side_channel_test import generate_cap_for_package_aid
from measurement_script import measure_cap_file
from trs_analyser import extract_from_single_trs_file

# generate CAP file
# get 10 measurements
# extract times
# calculate median from times
# check whether median fall in interval
# if yes:
    # add byte value to correct
# else:
    # continue

aid_len = 7
bytes_to_bruteforce = 5
measurements_for_one_byte = 10

index_to_extract = -1

major = 1
minor = 0
base_aid = bytearray.fromhex("A0" + "00" * (aid_len - 1))

result_file = open("bruteforce_results.csv", "w")
result_file_writer = csv.writer(result_file)

for byte_number in range(1, bytes_to_bruteforce - 1):
    for byte_value in range(256):
        current_aid = base_aid.copy()
        current_aid[byte_number] = byte_value
        print(f"Measuring: {current_aid.hex()}")
        cap_file_name = generate_cap_for_package_aid(current_aid, major, minor, byte_value, "bruteforce")
        measure_cap_file(cap_file_name, measurements_for_one_byte, "tmp_traces")
        times = extract_from_single_trs_file(measurements_for_one_byte, "tmp_traces/traces_bruteforce.trs", index_to_extract)
        median_time = median(times)
        print(f"AID: {current_aid.hex()}\n"
              f"Times: {times}\n"
              f"Median time: {median_time}\n\n")
        result_file_writer.writerow([byte_number, byte_value] + times)
        os.remove(cap_file_name)
        os.remove("tmp_traces/traces_bruteforce.trs")
    break



