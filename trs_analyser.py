import argparse
import os

import trsfile
import csv
import numpy as np
import numba
from numba.np.arrayobj import numpy_broadcast_arrays

SAMPLE_INTERVAL_NS = 25

MAX_GAP = 10_000_000 * 50/SAMPLE_INTERVAL_NS
MIN_DURATION = 150_000 * 50/SAMPLE_INTERVAL_NS
THRESHOLD_HIGH = 10

TRACE_TO_EXTRACT = -1

def extract_trace(filename: str, trace_index: int) -> list[int]:
    with trsfile.open(filename, 'r') as traces:
        return traces[trace_index]

def get_num_of_traces(filename: str) -> int:
    with trsfile.open(filename, 'r') as traces:
        return len(traces)


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

def find_high_consumption_periods(data, threshold=THRESHOLD_HIGH, min_duration=MIN_DURATION, max_gap=MAX_GAP):
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


def bulk_extract(traces_dirname: str, output_filename: str) -> tuple[int, int]:
    csv_file = open(output_filename, "w")
    csv_writer = csv.writer(csv_file)
    num_of_files = len(os.listdir(traces_dirname))

    for file_num, trs_file_name in enumerate(sorted(os.listdir(traces_dirname))):
        print(f"{file_num + 1}/{num_of_files}")
        trs_path = os.path.join(traces_dirname, trs_file_name)
        print(trs_path)
        num_of_traces_in_file = get_num_of_traces(trs_path)
        for trace_num in range(num_of_traces_in_file):
            print(f"{trace_num + 1}/{num_of_traces_in_file}")

            trace = extract_trace(trs_path, trace_num)

            periods = find_high_consumption_periods(trace)
            times = [period[1] - period[0] for period in periods]

            print(periods)
            print(times)
            csv_writer.writerow([file_num, trace_num] + times)
        csv_writer.writerow([])

    csv_file.close()
    return num_of_files, num_of_traces_in_file


def extract_single_response(response_index: int, input_filename: str, output_filename: str, num_of_files: int, number_of_traces_in_file: int) -> None:
    csv_file_read = open(input_filename, "r")
    csv_reader = csv.reader(csv_file_read)

    csv_file_write = open(output_filename, "w")
    csv_writer = csv.writer(csv_file_write)

    csv_writer.writerow(["modification"] + [i for i in range(1, num_of_traces_in_file + 1)])
    rows = [row for row in csv_reader if row]

    row_names = [f"AID {i}. byte" for i in range(1, num_of_files - 1)]
    row_names.extend([
        "Major version",
        "Minor version",
    ])

    for byte_changed in range(num_of_files):
        new_row = []
        for measurement in range(num_of_traces_in_file):
            new_row.append(rows[byte_changed * num_of_traces_in_file + measurement][response_index])
        csv_writer.writerow([row_names[byte_changed]] + new_row)

    csv_file_write.close()
    csv_file_read.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS analyser",
        description=""
    )

    parser.add_argument('-r', '--results_dirname', help='Directory with the TRS files', required=True)
    parser.add_argument('-o', '--output_filename', help='Filename for the complete CSV', required=True)
    parser.add_argument('-e', '--extract_filename', help='Filename for the CSV with extracted time', required=True)


    args = parser.parse_args()

    num_of_files, num_of_traces_in_file = bulk_extract(args.results_dirname, args.output_filename)

    extract_single_response(TRACE_TO_EXTRACT, args.output_filename, args.extract_filename, num_of_files, num_of_traces_in_file)

# import csv
#
# result_file = open("all.csv", "w")
# csv_writer = csv.writer(result_file)
# csv_writer.writerow(["modification"] + [i for i in range(1, 401)])
# row_names = [f"AID {i}. byte" for i in range(1, 8)]
# row_names.extend([
#     "Major version",
#     "Minor version",
# ])
#
# new_rows = [[row_name] for row_name in row_names]
# for i in range(9):
#     new_row = []
#     for changed_byte in ["ee", "ff"]:
#         for package_name in ["javacard_security", "javacardx_crypto"]:
#             full_name = f"/home/petr/Downloads/diplomka/new_results/feitian_k_9/{package_name}_{changed_byte}_extract.csv"
#             with open(full_name) as f:
#                 csv_reader = csv.reader(f)
#                 rows = list(csv_reader)
#                 rows = [row for row in rows if row[0] != 'modification']
#                 new_rows[i].extend(rows[i][1:])
#
# for row in new_rows:
#     csv_writer.writerow(row)
# print(new_rows)