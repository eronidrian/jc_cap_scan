import argparse
import os

import trsfile
import csv
import numpy as np
import numba

SAMPLE_INTERVAL_NS = 25

MAX_GAP = 5_000
MIN_DURATION = 200_000
THRESHOLD_HIGH = -15

TRACE_TO_EXTRACT = 1

SAMPLES_IN_TRACE = 25_000_010
TRACES_IN_FILE = 100


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
    data = np.fromiter(data, dtype=np.int8, count=SAMPLES_IN_TRACE)
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
    result_starts, result_ends = merge_gaps(starts, ends, max_gap)

    # Filter by min_duration
    result_starts = np.array(result_starts)
    result_ends = np.array(result_ends)
    durations = result_ends - result_starts
    valid = durations >= min_duration

    return list(zip(result_starts[valid], result_ends[valid] - 1))


def bulk_extract(traces_dirname: str, output_filename: str) -> int:
    csv_file = open(output_filename, "w")
    csv_writer = csv.writer(csv_file)
    num_of_files = len(os.listdir(traces_dirname))

    for file_num, trs_file_name in enumerate(sorted(os.listdir(traces_dirname))):
        print(f"{file_num + 1}/{num_of_files}")
        trs_path = os.path.join(traces_dirname, trs_file_name)
        traces = trsfile.open(trs_path, 'r')
        print(trs_path)
        for trace_num in range(TRACES_IN_FILE):
            print(f"{trace_num + 1}/{TRACES_IN_FILE}")

            trace = traces[trace_num]

            periods = find_high_consumption_periods(trace)
            times = [period[1] - period[0] for period in periods]
            print(periods)
            print(times)
            csv_writer.writerow([file_num, trace_num] + periods)
        csv_writer.writerow([])

    csv_file.close()
    return num_of_files


def extract_single_response(response_index: int, input_filename: str, output_filename: str, num_of_files: int) -> None:
    csv_file_read = open(input_filename, "r")
    csv_reader = csv.reader(csv_file_read)

    csv_file_write = open(output_filename, "w")
    csv_writer = csv.writer(csv_file_write)

    csv_writer.writerow(["modification"] + [i for i in range(1, TRACES_IN_FILE + 1)])
    rows = [row for row in csv_reader if row]

    row_names = [f"AID {i}. byte" for i in range(1, num_of_files - 1)]
    row_names.extend([
        "Major version",
        "Minor version",
    ])

    for byte_changed in range(num_of_files):
        new_row = []
        for measurement in range(TRACES_IN_FILE):
            if len(rows[byte_changed * TRACES_IN_FILE + measurement]) <= response_index:
                new_row.append(0)
            else:
                new_row.append(rows[byte_changed * TRACES_IN_FILE + measurement][response_index])
        csv_writer.writerow([row_names[byte_changed]] + new_row)

    csv_file_write.close()
    csv_file_read.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS analyser",
        description=""
    )

    parser.add_argument('-r', '--results_dirname', help='Directory with the TRS files', required=True)

    args = parser.parse_args()

    for package_name in ["javacard_security", "javacardx_crypto"]:
        for changed_byte_value in ["ee", "ff"]:
            current_dirname = os.path.join(args.results_dirname, f"{package_name}_{changed_byte_value}")
            num_of_files = bulk_extract(current_dirname, f"{package_name}_{changed_byte_value}_full.csv")
            # extract_single_response(TRACE_TO_EXTRACT, f"{package_name}_{changed_byte_value}_full.csv",
            #                         f"{package_name}_{changed_byte_value}_extract.csv", num_of_files)
