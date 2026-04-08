import argparse
from typing import Literal

import numpy as np
import trsfile
from matplotlib import pyplot as plt
from numpy import ndarray, mean
from sklearn.preprocessing import minmax_scale

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.trs_analysis.trs_extractor import find_high_consumption_periods
from jc_cap_scan.trs_analysis.trs_overlay import get_alignment_offset
from jc_cap_scan.utils.trs_utils import load_trs_file

align_to_start = True
anchor_index = 0 if align_to_start else -1
alignment_threshold = 0.6
align_to_start = True
ignore_last = 1_000_000
IGNORE_FIRST = 750_000


def ratio_diff(number_1: float, number_2: float) -> float:
    if number_1 > number_2:
        return number_1 / number_2
    if number_2 > number_1:
        return number_2 / number_1
    return 1


def get_diff_periods(samples_valid: ndarray, samples_invalid: ndarray, threshold: float,
                     config: ExtractionConfig) -> float | None:
    periods_valid = find_high_consumption_periods(samples_valid, config)
    periods_invalid = find_high_consumption_periods(samples_invalid, config)
    for i in range(len(periods_valid)):
        if i >= len(periods_invalid):
            return None
        duration_valid = periods_valid[i][1] - periods_valid[i][0]
        duration_invalid = periods_invalid[i][1] - periods_invalid[i][0]
        diff = ratio_diff(duration_valid, duration_invalid)
        if diff > threshold:
            return mean(periods_valid[i])
    return None


def get_diff_subtraction(samples_valid: ndarray, samples_invalid: ndarray, threshold: float,
                         show: bool) -> float | None:
    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, alignment_threshold, True)
    if offset_invalid_x is None:
        return None

    start = int(offset_invalid_x)
    end = start + len(samples_invalid)

    # prepare diff array same length as valid
    diff = samples_valid.copy()  # or np.empty_like(samples_valid) if you will overwrite all values

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
    diff[mask] = np.nan  # or leave as original values

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
    diff = diff[IGNORE_FIRST:]
    indices = np.where(diff >= threshold)[0]
    if not indices.size:
        return None
    return indices[0] + IGNORE_FIRST


def get_diff(path_valid: str, path_invalid: str, threshold: float, algorithm: Literal['subtraction', 'periods'],
             config: ExtractionConfig | None = None) -> float | None:
    assert algorithm in ['subtraction', 'periods']

    samples_valid = load_trs_file(path_valid, True)
    samples_invalid = load_trs_file(path_invalid, True)

    if algorithm == 'subtraction':
        return get_diff_subtraction(samples_valid, samples_invalid, threshold, False)
    elif algorithm == 'periods':
        return get_diff_periods(samples_valid, samples_invalid, threshold, config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS diff"
    )
    parser.add_argument("-v", "--valid", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("-i", "--invalid", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("-t", "--threshold", help="Threshold for the diff", type=float)
    parser.add_argument("--show", help="Show the resulting plot", action="store_true", required=False)
    parser.add_argument("--algorithm", help="One of 'subtraction' or 'periods'", required=True)
    parser.add_argument("--config", help="Path to config for the 'periods' algorithm", required=False)

    args = parser.parse_args()

    if args.algorithm == 'subtraction':
        if args.show:
            get_diff_subtraction(args.valid, args.invalid, args.threshold, True)
        elif not args.show:
            print(get_diff_subtraction(args.valid, args.invalid, args.threshold, False))
    elif args.algorithm == 'periods':
        print(get_diff_periods(args.valid, args.invalid, args.threshold, args.config))
