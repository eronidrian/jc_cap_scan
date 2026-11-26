import trsfile
import numpy as np
import bottleneck as bn
from scipy.signal import correlate

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.utils.trs_utils import load_single_trace_from_trs_file, load_all_traces_from_trs_file


def find_template_in_trace(trace: np.ndarray, template: np.ndarray) -> tuple[int, int]:
    n = len(template)

    # FFT correlation remains useful for long traces.
    corr = correlate(trace, template, mode="valid", method="fft")

    sums = bn.move_sum(trace, window=n)
    sums = sums[n - 1:]

    sums_sq = bn.move_sum(trace * trace, window=n)
    sums_sq = sums_sq[n - 1:]

    local_var = np.maximum(sums_sq - sums * sums / n, 1e-12)

    sqrt_var = np.sqrt(local_var)
    scores = corr / sqrt_var

    start = int(np.argmax(scores))
    return start, start + n

def find_segment_start_and_end_in_trace(trace: np.ndarray, start_template: np.ndarray, end_template: np.ndarray) -> tuple[int, int, int, int]:
    """
    Find start and end of a segment in a trace using a template for the start and end of the segment.
    :param trace: Power trace to search
    :param start_template: Template for the start of the segment
    :param end_template: Template for the end of the segment. Must be the same length as start segment.
    :return: Four tuple with start template start and end, and end template start and end
    """
    assert len(start_template) == len(end_template)

    n = len(start_template)

    # FFT correlation remains useful for long traces.
    corr_start = correlate(trace, start_template, mode="valid", method="fft")
    corr_end = correlate(trace, end_template, mode="valid", method="fft")

    sums = bn.move_sum(trace, window=n)
    sums = sums[n - 1:]

    sums_sq = bn.move_sum(trace * trace, window=n)
    sums_sq = sums_sq[n - 1:]

    local_var = np.maximum(sums_sq - sums * sums / n, 1e-12)

    sqrt_var = np.sqrt(local_var)
    scores_start = corr_start / sqrt_var
    scores_end = corr_end / sqrt_var

    start_1 = int(np.argmax(scores_start))
    start_2 = int(np.argmax(scores_end))
    return start_1, start_1 + n, start_2, start_2 + n


def extract_times_from_trs_file(trs_filename: str, extraction_config: ExtractionConfig) -> list[int]:
    """
     Extract durations of a segment in all traces from the TRS file. Uses template matching to find start and end of the segment.
     :param trs_filename: Path to the TRS file to extract the times from
     :param extraction_config: Config to use for the extraction
     :return: For each trace in the TRS file a duration of the segment in number of samples
     """

    result = []

    with trsfile.open(trs_filename, "r") as traces:
        for i, raw in enumerate(traces):
            print(f"Extracting {i + 1}/{len(traces)}")
            trace = np.asarray(raw, dtype=float)

            start_start, start_end, end_start, end_end = find_segment_start_and_end_in_trace(trace, extraction_config.start_template, extraction_config.end_template)
            duration = end_start - start_end
            result.append(duration)

    return result