import trsfile
import numpy as np
import numba

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.utils.trs_utils import load_trs_file


@numba.njit
def merge_gaps(starts, ends, max_gap):
    """
    Bridge gaps between periods that are smaller than or equal to max_gap. This is useful to bridge small gaps that can be caused by noise in the power trace.
    :param starts: Start of the periods
    :param ends: Ends of the periods
    :param max_gap: Max gap between periods to bridge
    :return: New starts and ends of the periods
    """
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


def find_high_consumption_periods(samples: np.ndarray, extraction_config: ExtractionConfig) -> list[tuple[int, int]]:
    """
    Find periods of high consumption in the power trace
    :param samples: Array of samples of the power trace
    :param extraction_config: Config to use for the extraction
    :return: Starts and ends of the high consumption periods
    """
    samples = np.fromiter(samples, dtype=np.float16, count=len(samples))
    high = samples > extraction_config.threshold

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
    result_starts, result_ends = merge_gaps(starts, ends, extraction_config.max_gap)

    # Filter by min_duration
    result_starts = np.array(result_starts)
    result_ends = np.array(result_ends)
    durations = result_ends - result_starts
    valid = durations >= extraction_config.min_duration

    return list(zip(result_starts[valid], result_ends[valid] - 1))

def extract_all_times_from_trs_file(trs_filename: str, extraction_config: ExtractionConfig) -> list[list[int]]:
    """
    Extract durations of all periods for all traces in the TRS file
    :param trs_filename: Path to the TRS file to extract the times from
    :param extraction_config: Config to use for the extraction
    :return: For each trace in the TRS file a list of durations of the periods
    """
    traces = trsfile.open(trs_filename, 'r')

    result = []

    for i, _ in enumerate(traces):

        trace = load_trs_file(trs_filename, True, i)

        periods = find_high_consumption_periods(trace, extraction_config)
        times = [period[1] - period[0] for period in periods]
        print(f"Extracting {i + 1}/{len(traces)}")
        print(len(times))
        result.append(times)

    return result


def extract_single_time_from_trs_file(trs_filename: str, extraction_config: ExtractionConfig) -> list[int]:
    """
    Extract only a single duration for each trace from the TRS file
    :param trs_filename: Path to TRS file
    :param extraction_config: Config to use for the extraction
    :return: For each trace in the TRS file a single duration of the period with index extraction_config.index_to_extract. If there is no such period, 0 is returned for that trace.
    """
    traces = trsfile.open(trs_filename, 'r')

    result = []

    for i, _ in enumerate(traces):

        trace = load_trs_file(trs_filename, True, i)

        periods = find_high_consumption_periods(trace, extraction_config)
        times = [period[1] - period[0] for period in periods]
        try:
            time = times[extraction_config.index_to_extract]
        except IndexError:
            time = 0

        print(f"Extracting {i + 1}/{len(traces)}")
        print(time)
        result.append(int(time))

    return result