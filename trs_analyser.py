import trsfile
import csv

MEASUREMENTS_FILENAME = "time_measurements.csv"
NUM_OF_TRACES_IN_FILE = 10
NUM_OF_CHANGED_BYTES = 9

def extract_trace(filename: str, trace_index: int) -> list[int]:
    with trsfile.open(filename, 'r') as traces:
        return traces[trace_index]


def smooth_high_periods(high_periods: list[bool], max_gap: int) -> list[bool]:
    result = high_periods[:]
    i = 0
    while i < len(result):
        if not result[i]:
            j = i
            while j < len(result) and not result[j] and (j - i) <= max_gap:
                j += 1
            if j < len(result) and result[i - 1] and result[j]:
                for k in range(i, j):
                    result[k] = True
            i = j
        else:
            i += 1
    return result


def filter_long_high_periods(high_periods_smoothed: list[bool], min_duration: int) -> list[tuple[int, int]]:
    periods = []
    start = None
    for i, is_high in enumerate(high_periods_smoothed):
        if is_high:
            if start is None:
                start = i
        else:
            if start is not None and i - start >= min_duration:
                periods.append((start, i - 1))
            start = None

    if start is not None and len(high_periods_smoothed) - start >= min_duration:
        periods.append((start, len(high_periods_smoothed) - 1))

    return periods

def bulk_process(traces_dirname: str, max_gap: int, min_duration: int, threshold_high: int):
    csv_file = open(MEASUREMENTS_FILENAME, "w")
    csv_writer = csv.writer(csv_file)

    for byte_changed in range(NUM_OF_CHANGED_BYTES):
        print(f"{byte_changed + 1}/{NUM_OF_CHANGED_BYTES}")
        for trace_num in range(NUM_OF_TRACES_IN_FILE):
            print(f"{trace_num + 1}/{NUM_OF_TRACES_IN_FILE}")
            filename = f'{traces_dirname}/{byte_changed}/all_traces_byte_{byte_changed}.trs'
            trace = extract_trace(filename, trace_num)

            high_periods = [x > threshold_high for x in trace]
            high_periods_smoothed = smooth_high_periods(high_periods, max_gap)
            periods = filter_long_high_periods(high_periods_smoothed, min_duration)

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
    rows = [row for row in csv_reader]

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


max_gap = 100_000
min_duration = 50_000
threshold_high = 6
results_dirname = '/home/petr/Downloads/diplomka/side_channel_measurement/results/25_MS_all_bytes_10_traces'

bulk_process(results_dirname, max_gap, min_duration, threshold_high)

