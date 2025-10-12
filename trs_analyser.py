import argparse
import os

import trsfile
import csv
import numpy as np
import numba


MAX_GAP = 10_000
MIN_DURATION = 50_000
THRESHOLD_HIGH = 0


SAMPLES_IN_TRACE = 25_000_010


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

def extract_from_single_trs_file(traces_in_file: int, filename: str, index_to_extract: int) -> list[int]:
    traces = trsfile.open(filename, 'r')

    result = []

    for trace_num in range(traces_in_file):
        trace = traces[trace_num]

        periods = find_high_consumption_periods(trace)
        times = [period[1] - period[0] for period in periods]
        if len(times) <= abs(index_to_extract):
            result.append(0)
        else:
            result.append(times[index_to_extract])

    return result