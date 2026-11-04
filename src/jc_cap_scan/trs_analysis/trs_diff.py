import argparse

import numpy as np
from matplotlib import pyplot as plt

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.trs_analysis.trs_overlay import get_alignment_offset
from jc_cap_scan.utils.trs_utils import load_single_trace_from_trs_file



def get_diff(path_valid: str, path_invalid: str, diff_threshold: float, show: bool, ignore_first_n : int,
             extraction_config: ExtractionConfig) -> float | None:
    """
    Get diff of two power traces using either the 'subtraction' or 'periods' algorithm
    :param path_valid: Path to valid trace (the base power trace)
    :param path_invalid: Path to invalid trace (the compared power trace)
    :param diff_threshold: Threshold to use for the diff
    :param show: Whether to show the diff
    :param ignore_first_n: Ignore the first n samples when looking for the diff
    :param extraction_config: Extraction config to get the template for the alignment
    :return:
    """

    samples_valid = load_single_trace_from_trs_file(path_valid, False)
    samples_invalid = load_single_trace_from_trs_file(path_invalid, False)

    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, extraction_config.start_template)
    if offset_invalid_x is None:
        return None

    start = int(offset_invalid_x)
    end = start + len(samples_invalid)

    # prepare diff array same length as valid
    diff = samples_valid.copy()

    # Case 1: invalid fully inside valid
    if start >= 0 and end <= len(samples_valid):
        diff[start:end] = samples_valid[start:end] - samples_invalid
    # Case 2: invalid starts before valid (clip left)
    elif start < 0 < end:
        left_clip = -start
        valid_slice = slice(0, min(end, len(samples_valid)))
        invalid_slice = slice(left_clip, left_clip + (valid_slice.stop - valid_slice.start))
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice])
    # Case 3: invalid starts inside but extends past valid (clip right)
    elif start < len(samples_valid) < end:
        valid_slice = slice(start, len(samples_valid))
        invalid_slice = slice(0, len(samples_valid) - start)
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice])
    # Case 4: invalid entirely outside valid -> no overlap
    else:
        # no overlap: diff is just the original valid (or you may want NaNs in non-overlap regions)
        pass

    # Optional: if you want diff only where overlap exists, set non-overlap to NaN
    overlap_start = max(0, start)
    overlap_end = min(len(samples_valid), end)
    mask = np.ones_like(diff, dtype=bool)
    mask[overlap_start:overlap_end] = False
    diff[mask] = np.nan

    diff = abs(diff)

    if show:
        fig, ax = plt.subplots()
        ax.plot(samples_valid, label='samples_valid')
        ax.plot(np.arange(start, end), samples_invalid, label='samples_invalid')
        ax.plot(diff, label='diff')
        ax.legend(loc='upper left')
        plt.show()

    if diff is None:
        return None
    diff = diff[ignore_first_n:]
    indices = np.where(diff >= diff_threshold)[0]
    if not indices.size:
        return None
    return indices[0] + ignore_first_n

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS diff"
    )
    parser.add_argument("-v", "--valid", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("-i", "--invalid", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("--diff_threshold", help="Threshold for the diff", type=float, required=True)
    parser.add_argument("--ignore_first_n", help="Ignore first n samples (for 'subtraction' algorithm)", type=int, required=False, default=0)
    parser.add_argument("--show", help="Show the resulting plot", action="store_true", required=False)
    parser.add_argument("--config", help="Path to extraction config to get the template", required=True)

    args = parser.parse_args()
    extraction_config = ExtractionConfig.load_from_toml(args.config)

    if args.show:
            get_diff(args.valid, args.invalid, args.diff_threshold, True, args.ignore_first_n, args.extraction_config)
    elif not args.show:
        print(get_diff(args.valid, args.invalid, args.diff_threshold,  False, args.ignore_first_n, args.extraction_config))
