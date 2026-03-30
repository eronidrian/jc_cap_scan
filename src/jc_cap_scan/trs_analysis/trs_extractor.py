import trsfile
import numpy as np
import numba

from jc_cap_scan.config.config import ExtractionConfig


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


def find_high_consumption_periods(data, threshold: int, min_duration: int, max_gap: int, samples_in_trace: int):

    data = np.fromiter(data, dtype=np.int8, count=samples_in_trace)
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

def extract_times_from_trs_file(filename: str, config: ExtractionConfig) -> list[int]:
    traces = trsfile.open(filename, 'r')

    result = []
    samples_in_trace = traces.get_headers().get(trsfile.Header.NUMBER_SAMPLES)

    for i, trace in enumerate(traces):

        periods = find_high_consumption_periods(trace, config.threshold, config.min_duration, config.max_gap, samples_in_trace)
        times = [period[1] - period[0] for period in periods]
        if len(times) < abs(config.index_to_extract):
            time = 0
        else:
            time = times[config.index_to_extract]
        print(f"Extracting {i + 1}/{len(traces)}")
        print(time)
        result.append(time)

    return result