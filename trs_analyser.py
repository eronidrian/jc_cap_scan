import trsfile
import csv
import numpy as np
import numba

MEASUREMENTS_FILENAME = "time_measurements.csv"
NUM_OF_TRACES_IN_FILE = 10
NUM_OF_CHANGED_BYTES = 11

PACKAGE_NAME = "javacardx_framework_util_intx"
CHANGED_BYTE = "ff"

def extract_trace(filename: str, trace_index: int) -> list[int]:
    with trsfile.open(filename, 'r') as traces:
        return traces[trace_index]


@numba.njit
def merge_gaps(starts, ends, max_gap):
    result_starts = []
    result_ends = []
    current_start = starts[0]
    current_end = ends[0]

    for i in range(1, len(starts)):
        if starts[i] - current_end <= max_gap:
            current_end = ends[i]
        else:
            result_starts.append(current_start)
            result_ends.append(current_end)
            current_start = starts[i]
            current_end = ends[i]

    result_starts.append(current_start)
    result_ends.append(current_end)

    return result_starts, result_ends

def find_high_consumption_periods(data, threshold, min_duration, max_gap):
    data = np.asarray(data)
    high = data > threshold

    # Detect rising and falling edges
    diff = np.diff(high.astype(np.int8))
    starts = np.flatnonzero(diff == 1) + 1
    ends = np.flatnonzero(diff == -1) + 1

    # Edge case: high at start or end
    if high[0]:
        starts = np.insert(starts, 0, 0)
    if high[-1]:
        ends = np.append(ends, len(high))

    # Merge small gaps
    starts, ends = merge_gaps(starts, ends, max_gap)

    # Filter by min_duration
    starts = np.array(starts)
    ends = np.array(ends)
    durations = ends - starts
    valid = durations >= min_duration

    return list(zip(starts[valid], ends[valid] - 1))


def bulk_process(traces_dirname: str, max_gap: int, min_duration: int, threshold_high: int):
    csv_file = open(MEASUREMENTS_FILENAME, "w")
    csv_writer = csv.writer(csv_file)

    for byte_changed in range(NUM_OF_CHANGED_BYTES):
        print(f"{byte_changed + 1}/{NUM_OF_CHANGED_BYTES}")
        for trace_num in range(NUM_OF_TRACES_IN_FILE):
            print(f"{trace_num + 1}/{NUM_OF_TRACES_IN_FILE}")
            filename = f'{traces_dirname}/all_traces_{PACKAGE_NAME}_{byte_changed}_{CHANGED_BYTE}.trs'
            trace = extract_trace(filename, trace_num)

            periods = find_high_consumption_periods(trace, threshold_high, min_duration, max_gap)
            times = [period[1] - period[0] for period in periods]

            print(periods)
            print(times)
            csv_writer.writerow([byte_changed, trace_num] + times)
        csv_writer.writerow([])

    csv_file.close()


def extract_single_response(response_index: int, output_filename: str) -> None:
    csv_file_read = open(MEASUREMENTS_FILENAME, "r")
    csv_reader = csv.reader(csv_file_read)

    csv_file_write = open(output_filename, "w")
    csv_writer = csv.writer(csv_file_write)

    csv_writer.writerow(["modification"] + [i for i in range(1, NUM_OF_TRACES_IN_FILE + 1)])
    rows = [row for row in csv_reader if row]

    row_names = [f"AID {i}. byte" for i in range(1, NUM_OF_CHANGED_BYTES - 1)]
    row_names.extend([
        "Major version",
        "Minor version",
    ])

    for byte_changed in range(NUM_OF_CHANGED_BYTES):
        new_row = []
        for measurement in range(NUM_OF_TRACES_IN_FILE):
            new_row.append(rows[byte_changed * NUM_OF_TRACES_IN_FILE + measurement][response_index])
        csv_writer.writerow([row_names[byte_changed]] + new_row)

    csv_file_write.close()
    csv_file_read.close()


max_gap = 300_000
min_duration = 150_000
threshold_high = 6
results_dirname = f'/home/petr/Downloads/diplomka/side_channel_measurement/results/new/{PACKAGE_NAME}_{CHANGED_BYTE}'

bulk_process(results_dirname, max_gap, min_duration, threshold_high)

# extract_single_response(-1, f"aid_upload_times_{PACKAGE_NAME}_last.csv")

# result_file = open("all.csv", "w")
# csv_writer = csv.writer(result_file)
# csv_writer.writerow(["modification"] + [i for i in range(1, 41)])
# row_names = [f"AID {i}. byte" for i in range(1, NUM_OF_CHANGED_BYTES - 1)]
# row_names.extend([
#     "Major version",
#     "Minor version",
# ])
#
# base_name = "results_sca_new"
# new_rows = [[row_name] for row_name in row_names]
# for i in range(9):
#     new_row = []
#     for changed_byte in ["results_ee", "results_ff"]:
#         for package_name in ["javacard_security", "javacardx_crypto"]:
#             full_name = f"{base_name}/{changed_byte}/aid_upload_times_{package_name}_last.csv"
#             with open(full_name) as f:
#                 csv_reader = csv.reader(f)
#                 rows = list(csv_reader)
#                 rows = [row for row in rows if row[0] != 'modification']
#                 new_rows[i].extend(rows[i][1:])
#
# for row in new_rows:
#     csv_writer.writerow(row)
# print(new_rows)