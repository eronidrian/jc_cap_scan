import trsfile
import csv

def open_trsfile(filename: str) -> list[int]:
    with trsfile.open(filename, 'r') as traces:
        return traces[0]


def smooth_high(high: list[bool], max_gap: int) -> list[bool]:
    result = high[:]
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


def filter_high(high_smoothed: list[bool], min_duration: int) -> list[tuple[int, int]]:
    periods = []
    start = None
    for i, is_high in enumerate(high_smoothed):
        if is_high and start is None:
            start = i
        else:
            if start is not None and i - start >= min_duration:
                periods.append((start, i - 1))
            start = None

    if start is not None and len(high_smoothed) - start >= min_duration:
        periods.append((start, len(high_smoothed) - 1))

    return periods

max_gap = 100_000
min_duration = 150_000
threshold = 7

csv_file = open("time_measurements.csv", "w")
csv_writer = csv.writer(csv_file)

for i in range(9):
    filename = f'/home/petr/Downloads/diplomka/side_channel_measurement/results/{i}/all_traces.trs'
    trace = open_trsfile(filename)

    high = [x > threshold for x in trace[:40_000_000]]
    high_smoothed = smooth_high(high, max_gap)
    periods = filter_high(high_smoothed, min_duration)

    times = [period[1] - period[0] for period in periods]
    print(times)
    csv_writer.writerow(times)

